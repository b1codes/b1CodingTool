# GCP: Agent Commands & Skills

## Recommended Skills
- **Infrastructure Auditor:** Scans Terraform or Deployment Manager files for insecure configurations (e.g., overly broad IAM bindings, public GCS buckets).
- **Cloud Run Config Generator:** Assists in creating `service.yaml` manifests for Cloud Run deployments.
- **GKE Manifest Generator:** Generates Kubernetes `Deployment` and `Service` manifests tailored to GKE (Workload Identity, node pools, autoscaling).
- **Firebase Config Generator:** Helps generate `firebase.json` and `.firebaserc` for Hosting, Functions, and Firestore rules deployment.

## Common Agent Commands
- `/gcp audit`: Trigger a security audit of the `infrastructure/gcp/` directory.
- `/gcp cloud-run-init`: Generate a boilerplate Cloud Run `service.yaml` manifest.
- `/gcp gke-init`: Generate boilerplate GKE `Deployment` and `Service` manifests.
- `/gcp firebase-init`: Generate a boilerplate `firebase.json` and `.firebaserc`.

## Sync with b1
- `b1 install gcp`: Initializes the `infrastructure/gcp` directory structure and adds GCP-specific agent context.
- `b1 pair`: Ensures that GCP deployment guidelines are synchronized across all agent-specific instruction files.
