# GCP: Conventions

## Resource Naming
- **Uniqueness:** Use a consistent naming scheme that includes the project name and environment (e.g., `b1coding-prod-orders-bucket`). GCS bucket names are globally unique across all of Google Cloud.
- **Casing:** Use `kebab-case` for GCP resource names (services, buckets, clusters) and `snake_case` for Terraform resource identifiers.

## Labeling Strategy
Required labels for all resources:
| Label | Purpose | Example |
|-------|---------|---------|
| `project` | Identifier for the project | `b1codingtool` |
| `environment` | Deploy stage | `dev`, `staging`, `prod` |
| `owner` | Responsible team or person | `platform-team` |
| `managed-by` | Tool used for management | `terraform`, `gcloud` |

## Directory Structure (IaC)
Recommended layout for infrastructure files:
```
infrastructure/
├── gcp/
│   ├── base/           # VPC, IAM, shared service accounts
│   ├── modules/        # Reusable Terraform modules
│   └── services/       # Feature-specific infrastructure
│       ├── cloud-run.tf
│       └── gke-cluster.tf
└── variables/          # Environment-specific params
    ├── dev.tfvars
    └── prod.tfvars
```

## Region & Zone Selection
- **Proximity:** Deploy resources in regions closest to your user base to minimize latency.
- **Compliance:** Ensure the selected region meets any data residency requirements.
- **Zonal Redundancy:** For GKE, prefer regional clusters (spanning multiple zones) over zonal clusters for production workloads.

## Firebase-Specific Conventions
- Keep `firebase.json` and `.firebaserc` at the repository root so the Firebase CLI can be run without `--config` flags.
- Use Firebase project aliases (`default`, `staging`, `prod`) in `.firebaserc` to switch environments via `firebase use <alias>` instead of hardcoding project IDs in scripts.
