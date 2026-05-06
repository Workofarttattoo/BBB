# Azure Container Apps deployment

This repo can deploy the public BBB API and the private Echo Prime orchestrator
to Azure Container Apps using
`.github/workflows/azure-container-app.yml`.

## Required GitHub variables

- `AZURE_RESOURCE_GROUP`
- `AZURE_CONTAINER_APP_NAME` - public BBB FastAPI app
- `AZURE_ECHO_PRIME_APP_NAME` - private Echo Prime app, defaults to `echo-prime`
- `AZURE_CONTAINER_APP_ENVIRONMENT`
- `AZURE_CONTAINER_REGISTRY` - ACR name without `.azurecr.io`
- `AZURE_LOCATION` - optional, defaults to `eastus`
- `CORS_ORIGINS` - comma-separated allowed browser origins
- `ECH0_LLM_PROVIDER` - optional, defaults to `ollama`
- `ECH0_LLM_ENDPOINT` - optional cloud/private model endpoint

## Required GitHub secrets

- `AZURE_CREDENTIALS` - JSON credentials for `azure/login`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `APOLLO_API_KEY`
- `ELEVENLABS_API_KEY`
- `ECH0_LLM_API_KEY` - optional, only needed when the Echo Prime model endpoint requires it

## Runtime notes

- The same image runs both services. `APP_MODULE` and `PORT` select the process:
  - BBB API: `blank_business_builder.main:app` on port `8000`
  - Echo Prime: `blank_business_builder.echo_prime_api:app` on port `8001`
- Echo Prime is created with internal ingress so it is reachable from BBB inside
  the Container Apps environment, but is not public.
- BBB is created with external ingress and receives `ECHO_BASE_URL` and
  `ECHO_PRIME_BASE_URL` from the private Echo Prime app FQDN.
- Both services expose `/health`.
- Apollo lead discovery is available at `/api/v1/outreach/discover`.
- ElevenLabs voice asset generation is available at
  `/api/v1/outreach/create-elevenlabs-audio`.
- Batch Apollo discovery plus ElevenLabs voice drafts is available at
  `/api/v1/outreach/discover-and-create-elevenlabs-audio`.

The ElevenLabs endpoints require `consent_confirmed=true`; they create audio
assets and database outreach records, but do not place outbound calls.

## Echo Prime orchestration routes

BBB calls Echo Prime through `EchoMasterBrain` for autonomous decisions:

- `/internal/echo/outreach-decision`
- `/internal/echo/post-call-decision`
- `/v1/businesses/recommendations`
- `/v1/businesses/validate`
- `/v1/chat`

If Echo Prime is temporarily unavailable, BBB still falls back to deterministic
local heuristics so outreach workflows degrade safely instead of crashing.
