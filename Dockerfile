# App image. The compiled engine lives in the base image, so UI and Python
# changes rebuild only this thin layer. Rebuild the base with:
#   gcloud builds submit --config cloudbuild.engine.yaml --ignore-file=.gcloudignore.engine .
FROM us-central1-docker.pkg.dev/<your-gcp-project>/cloud-run-source-deploy/clothoid-engine:2026-10-26

WORKDIR /app
COPY clothoid_lab /app/clothoid_lab
COPY web /app/web
COPY out/caps /app/out/caps
