# Terraform: Agent Commands & Skills

## Recommended Skills
- **State Backend Configurator:** Scaffolds a remote state `backend.tf` (S3+DynamoDB lock, GCS, or Azure Storage) with locking enabled.
- **Project Scaffolder:** Generates root Terraform boilerplate (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`) plus per-environment `.tfvars`.
- **Infrastructure Auditor:** Reviews `.tf` files for insecure defaults, hardcoded secrets, unpinned provider/module versions, and missing state locking.

## Common Agent Commands
These commands are run by the agent (not the `b1` CLI) when the user asks for them by name — the agent locates and executes the matching script under `scripts/`, the same mechanism used by the `gcp` and `aws` modules:
- `/terraform backend-init`: Run `scripts/backend-init.sh` to generate `infrastructure/terraform/backend.tf` for S3, GCS, or Azure Storage.
- `/terraform project-init`: Run `scripts/project-init.sh` to generate the root module files and `environments/*.tfvars`.
- `/terraform audit`: Review the `infrastructure/terraform/` directory against `best-practices.md` and report findings — no script backs this command; it is a review task performed directly by the agent.

## Sync with b1
- `b1 install terraform`: Initializes the `infrastructure/terraform` directory structure and adds Terraform-specific agent context.
- `b1 pair`: Ensures Terraform conventions and best practices are synchronized across all agent-specific instruction files.
