# Terraform: Best Practices

## State Management
- **Remote State:** Never rely on local state for anything beyond a personal sandbox. Store state in a remote backend (S3, GCS, Azure Storage) from the first commit.
- **Locking:** Ensure the backend enforces state locking (DynamoDB table for S3, native locking for GCS/Azure) to prevent concurrent `apply` corruption.
- **Never Commit State:** `.tfstate` and `.tfstate.backup` must never be committed to git — they can contain secrets in plaintext. Add them to `.gitignore`.
- **Isolate State per Environment:** Use separate state files (via workspaces or separate backend keys/prefixes) per environment so a mistake in `dev` cannot touch `prod`.

## Version Pinning
- **Terraform Core:** Pin `required_version` in `versions.tf` to a specific minimum (e.g., `>= 1.7.0`).
- **Providers:** Pin provider versions with `~>` (pessimistic constraint) rather than leaving them unbounded.
- **Modules:** Pin any module source to a specific tag or commit SHA — never track a branch in production.
- **Commit the Lock File:** `.terraform.lock.hcl` must be committed so every teammate and CI run resolves identical provider versions.

## Workflow
- **Plan Before Apply:** Always review `terraform plan` output before `terraform apply`. In CI, require a plan artifact to be attached to the PR before merge.
- **Code Review for Infra:** Treat `.tf` changes like application code — require review before merge, not just before apply.
- **No Manual Console Changes:** Once a resource is under Terraform management, all changes go through Terraform. Manual out-of-band changes cause drift.
- **Small, Focused Changesets:** Prefer many small plans over one sweeping plan touching unrelated resources — smaller blast radius when something goes wrong.

## Security
- **No Hardcoded Secrets:** Never put credentials, API keys, or passwords directly in `.tf` or `.tfvars` files. Reference them from a secret manager (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault) via a data source.
- **Restrict Backend Access:** The bucket/container holding remote state should have access limited to CI and the infra team — state files often contain sensitive attribute values.
- **Least Privilege for CI:** The service principal/role Terraform runs as in CI should have only the permissions its plans actually need, scoped per environment.

## Validation & Linting
- Run `terraform fmt -check` and `terraform validate` in CI on every PR.
- Use a static analyzer (`tflint`, `checkov`, or `tfsec`) to catch insecure defaults before they reach `plan`.
