# GCP: Best Practices

## Infrastructure as Code (IaC)
- **Declarative over Imperative:** Use Terraform or Google Cloud Deployment Manager for all production infrastructure. Avoid manual changes via the Cloud Console in production projects.
- **Version Control:** Commit all IaC templates to the repository and drive deployments through CI/CD (e.g., Cloud Build, GitHub Actions).
- **Project Structure:** Separate environments (dev/staging/prod) into distinct GCP projects rather than relying on naming conventions within a single project.

## Security & IAM
- **Principle of Least Privilege:** Grant only the minimum roles required for a task. Prefer predefined or custom IAM roles over primitive roles (Owner/Editor/Viewer).
- **Workload Identity:** Use Workload Identity Federation for GKE workloads and CI/CD instead of downloading long-lived service account keys.
- **Secret Management:** Use Secret Manager for sensitive configuration; never hardcode secrets in code, IaC templates, or container images.
- **Encryption by Default:** Enable CMEK (Customer-Managed Encryption Keys) for GCS buckets and persistent disks where compliance requires it.

## Compute Selection
Match the compute type to the workload:
- **Cloud Run:** Stateless, request-driven containers with automatic scale-to-zero.
- **GKE:** Long-running, stateful, or complex multi-service workloads needing full Kubernetes control.
- **Cloud Functions:** Small, event-driven single-purpose functions.
- **Firebase Hosting + Functions:** Static/SPA frontends paired with lightweight serverless backends.

## Performance & Scalability
- **Autoscaling:** Configure min/max instance counts on Cloud Run and Horizontal Pod Autoscalers on GKE to handle fluctuating demand.
- **Regional Placement:** Co-locate Cloud Run services, GKE clusters, and their backing databases in the same region to minimize latency and egress cost.

## Cost Optimization
- **Labeling:** Apply consistent labels (e.g., `environment`, `project`, `owner`) to all resources for cost allocation and Billing reports.
- **Right-sizing:** Use GKE node auto-provisioning and Cloud Run concurrency settings to avoid over-provisioning.
- **Budgets & Alerts:** Configure budget alerts in Cloud Billing to catch runaway spend early.
