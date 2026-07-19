# Terraform: Conventions

## Naming
- **Resource & Variable Names:** Use `snake_case` for all Terraform identifiers (resource names, variable names, output names) — this is the idiomatic HCL convention regardless of the cloud provider.
- **Resource Naming Pattern:** `<resource_type>.<purpose>`, e.g. `aws_s3_bucket.orders_archive`, not generic names like `bucket1`.

## Directory Structure
Recommended layout for a Terraform-managed root module:
```
infrastructure/terraform/
├── main.tf              # root module: wires together child modules
├── variables.tf         # root-level input variables (with descriptions)
├── outputs.tf           # root-level outputs
├── versions.tf          # required_version + required_providers
├── backend.tf           # remote state backend configuration
├── modules/             # reusable child modules
│   └── <module-name>/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/         # per-environment tfvars
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

## Relationship to Cloud-Specific Modules (gcp, aws)
This module owns the **generic** Terraform layer under `infrastructure/terraform/` — state backend, root module scaffolding, and cross-cloud conventions. The `gcp` and `aws` deployment modules document their **own** provider-specific resource layouts (e.g. `infrastructure/gcp/{base,modules,services}`) for the actual `provider` blocks and cloud resources. If a project installs `terraform` alongside `gcp` and/or `aws`, treat `infrastructure/terraform/` as the root module and reference the cloud module's resource definitions as child modules or provider-specific `.tf` files within it — the two are complementary layers, not competing conventions.

## Variables & Outputs
- Every variable and output **must** have a `description`. A variable without a description is a review-blocking omission, not a style nit.
- Provide sensible `default` values only for genuinely optional settings; required settings (project IDs, environment names) should have no default so `terraform plan` fails loudly if omitted.
- Mark sensitive variables (credentials, connection strings) with `sensitive = true`.

## Tagging / Labeling
Apply consistent tags/labels to every resource, mirrored across providers:
| Tag/Label | Purpose | Example |
|-----------|---------|---------|
| `project` | Identifier for the project | `b1codingtool` |
| `environment` | Deploy stage | `dev`, `staging`, `prod` |
| `owner` | Responsible team or person | `platform-team` |
| `managed-by` | Always `terraform` for Terraform-managed resources | `terraform` |

## Environment Isolation
- Prefer **separate `.tfvars` files per environment** (`environments/dev.tfvars`, etc.) driven by `terraform plan -var-file=environments/dev.tfvars`, over relying solely on Terraform workspaces — tfvars files are explicit and diffable in code review; workspaces hide the active environment in local shell state.
