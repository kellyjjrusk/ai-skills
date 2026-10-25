# Module patterns

## sitecore.json

```json
{
  "$schema": "./.sitecore/schemas/RootConfigurationFile.schema.json",
  "modules": [ "src/*/*/*.module.json" ],
  "plugins": [
    "Sitecore.DevEx.Extensibility.Serialization@<version>",
    "Sitecore.DevEx.Extensibility.Publishing@<version>",
    "Sitecore.DevEx.Extensibility.Indexing@<version>",
    "Sitecore.DevEx.Extensibility.ResourcePackage@<version>",
    "Sitecore.DevEx.Extensibility.XMCloud@<version>"
  ],
  "serialization": {
    "defaultMaxRelativeItemPathLength": 100,
    "defaultModuleRelativeSerializationPath": "serialization",
    "removeOrphansForRoles": true,
    "continueOnItemFailure": false,
    "excludedFields": []
  }
}
```

Pin plugin versions to the CLI version in `.config/dotnet-tools.json`; mismatched plugin and CLI versions are a common cause of opaque push failures.

## Feature module (developer-owned definitions)

```json
{
  "namespace": "Feature.Promotions",
  "references": [ "Foundation.*" ],
  "items": {
    "includes": [
      { "name": "templates",  "path": "/sitecore/templates/Feature/Promotions" },
      { "name": "renderings", "path": "/sitecore/layout/Renderings/Feature/Promotions" },
      { "name": "placeholders", "path": "/sitecore/layout/Placeholder Settings/Feature/Promotions" }
    ]
  }
}
```

## Project/site module with seeded content (authors own after first deploy)

```json
{
  "namespace": "Project.Acme",
  "references": [ "Feature.*", "Foundation.*" ],
  "items": {
    "includes": [
      { "name": "templates", "path": "/sitecore/templates/Project/Acme" },
      {
        "name": "site",
        "path": "/sitecore/content/Acme/AcmeSite",
        "scope": "ItemAndDescendants",
        "allowedPushOperations": "CreateOnly",
        "rules": [
          { "path": "/Settings", "scope": "ItemAndDescendants", "allowedPushOperations": "CreateAndUpdate" },
          { "path": "/Presentation", "scope": "ItemAndDescendants", "allowedPushOperations": "CreateUpdateAndDelete" },
          { "path": "/Home", "scope": "SingleItem", "allowedPushOperations": "CreateOnly" },
          { "path": "/Data", "scope": "Ignored" },
          { "path": "/Media", "scope": "Ignored" }
        ]
      }
    ]
  }
}
```

Rule paths are relative to the include path. Rules evaluate in order; first match wins.

## Roles

```json
{
  "namespace": "Foundation.Security",
  "roles": [
    { "domain": "sitecore", "pattern": "Acme *" }
  ]
}
```

Item-level access rights live in `__Security` fields on the items themselves, so they serialize with the items.

## Unicorn → SCS

| Unicorn | SCS |
|---|---|
| `<configuration name="Feature.X">` | `namespace: "Feature.X"` |
| `dependencies="Foundation.*"` | `references: ["Foundation.*"]` |
| `<include name="T" database="master" path="/x">` | include `{ name, database, path }` |
| `<exclude children="true" />` | `scope: "SingleItem"` or `"ItemAndChildren"` |
| `<exclude path="/x/y" />` | rule `{ path: "/y", scope: "Ignored" }` |
| `<except name="z" />` inside exclude | rule ordering: specific include rule before broader Ignored rule |
| NewItemOnlyEvaluator | `allowedPushOperations: "CreateOnly"` |
| SerializationPresetPredicate roles | `roles` section |
| Transparent Sync | none — use `ser push` or items as resources |

Steps: run both side by side in a branch; `ser pull` fresh from a synced dev DB; diff item counts per path between `Unicorn/**.yml` and SCS `serialization/**.yml`; delete Unicorn configs and NuGet packages from CM; remove from CD. Unicorn YAML is **not** byte-compatible with SCS YAML — always re-pull.

## TDS → SCS

| TDS | SCS |
|---|---|
| `.scproj` per project | `*.module.json` per module |
| Item deployment property `AlwaysUpdate` | `CreateUpdateAndDelete` / `CreateAndUpdate` |
| `DeployOnce` | `CreateOnly` |
| Code generation (T4/Glass) | drop for headless; or use separate codegen from YAML |
| Update packages (.update) | `ser package create` / items as resources |
