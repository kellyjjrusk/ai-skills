# Pipeline templates

Verify CLI flags with `dotnet sitecore <command> --help` for the pinned version; flags have changed across 5.x/6.x.

## .config/dotnet-tools.json

```json
{
  "version": 1,
  "isRoot": true,
  "tools": {
    "sitecore.cli": { "version": "<pinned>", "commands": [ "sitecore" ] }
  }
}
```

## GitHub Actions — SitecoreAI

```yaml
name: deploy-sitecoreai
on:
  push:
    branches: [ main ]
  workflow_dispatch:

concurrency:
  group: sitecoreai-${{ github.ref }}
  cancel-in-progress: false

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '8.0.x' }
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: dotnet tool restore
      - run: dotnet sitecore ser validate
      - run: python3 tools/analyze_scs.py . --out scs-report.md --fail-on-critical   # copy scripts/analyze_scs.py from this skill into tools/
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: scs-report, path: scs-report.md }

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with: { dotnet-version: '8.0.x' }
      - run: dotnet tool restore
      - name: Login (automation client)
        run: >
          dotnet sitecore cloud login --client-credentials
          --client-id "${{ secrets.SITECORE_CLIENT_ID }}"
          --client-secret "${{ secrets.SITECORE_CLIENT_SECRET }}"
          --allow-write true
      - name: Deploy
        id: deploy
        run: |
          dotnet sitecore cloud deployment create \
            --environment-id "${{ vars.SITECORE_ENVIRONMENT_ID }}" \
            --upload --json | tee deploy.json
      - name: Fetch logs
        if: always()
        run: |
          ID=$(python3 -c "import json;d=json.load(open('deploy.json'));print(d.get('id') or d.get('deploymentId',''))" 2>/dev/null || true)
          if [ -n "$ID" ]; then dotnet sitecore cloud deployment log --deployment-id "$ID" -o deploy-logs; fi
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: deploy-logs, path: deploy-logs }
```

If `--json` is not supported on the pinned CLI, capture the deployment ID from console output or call `cloud deployment list --environment-id` and take the newest.

## Azure DevOps — XM/XP (files + ser push)

```yaml
trigger: [ main ]
pool: { vmImage: windows-latest }

variables:
  - group: sitecore-prod   # CM_URL, ID_URL, CLIENT_ID, CLIENT_SECRET (secret)

stages:
- stage: Build
  jobs:
  - job: build
    steps:
    - task: UseDotNet@2
      inputs: { version: '8.0.x' }
    - script: dotnet tool restore
    - script: dotnet sitecore ser validate
    - task: MSBuild@1
      inputs:
        solution: '**/*.sln'
        msbuildArguments: '/p:Configuration=Release /p:DeployOnBuild=true /p:PublishProfile=FolderProfile /p:PublishUrl=$(Build.ArtifactStagingDirectory)\web'
    - script: dotnet sitecore itemres create -o $(Build.ArtifactStagingDirectory)\web\App_Data\items --overwrite
      displayName: Items as resources (optional alternative to ser push)
    - publish: $(Build.ArtifactStagingDirectory)
      artifact: drop

- stage: Deploy
  dependsOn: Build
  jobs:
  - deployment: cm
    environment: sitecore-prod
    strategy:
      runOnce:
        deploy:
          steps:
          - checkout: self
          - script: dotnet tool restore
          # deploy files to CM/CD with your existing task (WebDeploy, AzureRmWebAppDeployment, robocopy)
          - script: >
              dotnet sitecore login --client-credentials true
              --auth $(ID_URL) --cm $(CM_URL)
              --client-id $(CLIENT_ID) --client-secret $(CLIENT_SECRET)
              --allow-write true
          - script: dotnet sitecore ser push
          - script: dotnet sitecore publish --pt Smart
          - script: dotnet sitecore index rebuild
            condition: eq(variables['REBUILD_INDEXES'], 'true')
```

The CM must have a client-credentials client registered in Identity Server (`Sitecore.IdentityServer.Host.xml` / `Config/production/Sitecore.IdentityServer.DevEx.xml` with `ClientCredentials` grant). Without it, `login --client-credentials` returns `invalid_client`.

## Gates worth adding

- Fail on `ser validate` errors
- Fail on `analyze_scs.py --fail-on-critical`
- Require manual approval for production environment
- Post-deploy smoke test: curl home page and one deep page; check 200 and a known marker
