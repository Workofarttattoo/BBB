# Azure Container Apps deployment

This repo can deploy the FastAPI app to Azure Container Apps using
`.github/workflows/azure-container-app.yml`.

## Required GitHub variables

- `AZURE_RESOURCE_GROUP`
- `AZURE_CONTAINER_APP_NAME`
- `AZURE_CONTAINER_APP_ENVIRONMENT`
- `AZURE_CONTAINER_REGISTRY` - ACR name without `.azurecr.io`
- `AZURE_LOCATION` - optional, defaults to `eastus`
- `ECHO_BASE_URL` - public app URL after DNS is assigned
- `CORS_ORIGINS` - comma-separated allowed browser origins

## Required GitHub secrets

- `AZURE_CREDENTIALS` - JSON credentials for `azure/login`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `APOLLO_API_KEY`
- `ELEVENLABS_API_KEY`

## Runtime notes

- The container listens on port `8000` and exposes `/health`.
- Apollo lead discovery is available at `/api/v1/outreach/discover`.
- ElevenLabs voice asset generation is available at
  `/api/v1/outreach/create-elevenlabs-audio`.
- Batch Apollo discovery plus ElevenLabs voice drafts is available at
  `/api/v1/outreach/discover-and-create-elevenlabs-audio`.

The ElevenLabs endpoints require `consent_confirmed=true`; they create audio
assets and database outreach records, but do not place outbound calls.
