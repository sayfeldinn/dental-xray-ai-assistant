# Deployment

| Part | Where | Access |
| --- | --- | --- |
| Clinician UI | Cloudflare Pages, project `dentalai` → https://dentalai-49y.pages.dev | public |
| Backend API | Cloud Run `dentalai-backend` (europe-west1) | public; every route checks the Supabase login |
| ML service | Cloud Run `dentalai-ml` (europe-west1) | private: only the backend's service account may call it |
| Database, auth, X-rays | Supabase (eu-west-1) | RLS, private bucket, signed URLs |

Both Cloud Run services scale to zero, so the first request after a quiet period waits
for a cold start (the ML service loads PyTorch and four models). Open the app a minute
before a demo.

## First deploy

```bash
gcloud auth login                                   # once
deploy/deploy_cloud_run.sh <gcp-project-id> https://dentalai-49y.pages.dev
npx wrangler login                                  # once
deploy/deploy_frontend.sh <backend-url printed above>
```

`deploy_cloud_run.sh` builds both images in Cloud Build (the weights come from the
`weights-v3` Release and are checksum-verified there), stores the Supabase service-role
key in Secret Manager, and deploys the ML service private and the backend public. Re-running
it deploys the current commit.

Then, once, in the Supabase dashboard → **Authentication → URL Configuration**: set the
**Site URL** to `https://dentalai-49y.pages.dev` and add it under **Redirect URLs**, so
sign-up confirmation and password-reset emails link to the deployed app.

## Checks

```bash
backend/venv/bin/python scripts/e2e_cloud_flow.py .env /path/to/val_28.png   # BACKEND_URL=<cloud url> for the deployed API
```

## Cost

Within the free tiers at demo traffic (Cloud Run requests and CPU, Cloud Build minutes,
Cloudflare Pages). Artifact Registry stores the ~1 GB ML image beyond its 0.5 GB free
allowance: a few cents a month.

## Notes

- The ML service's feedback CSV lives on the container's in-memory disk and is lost when
  the instance stops; the authoritative record is the `clinical_feedback_logs` table.
- The Cloudflare account also hosts an unrelated Worker; these scripts only touch the
  `dentalai` Pages project.
