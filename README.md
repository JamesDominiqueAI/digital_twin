# Digital Twin — AI-Powered Personal Assistant

An AI digital twin that represents you on your personal website. Visitors can chat with it and learn about your background, skills, and experience. Built with FastAPI, OpenAI, Next.js, and deployed on AWS via Terraform.

---

## Architecture

```
User → CloudFront → S3 (Next.js frontend)
                 ↓
           API Gateway → Lambda (FastAPI + OpenAI)
                                ↓
                           S3 (conversation memory)
```

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, Tailwind CSS |
| Backend | FastAPI, Python 3.12, Mangum |
| AI | OpenAI GPT-4o-mini (configurable) |
| Memory | S3 (per-session conversation history) |
| Infra | AWS Lambda, API Gateway, CloudFront, S3 |
| IaC | Terraform (multi-workspace: dev / test / prod) |
| CI/CD | GitHub Actions + OIDC (no long-lived credentials) |

---

## Project Structure

```
.
├── backend/
│   ├── server.py           # FastAPI app (chat endpoint)
│   ├── context.py          # System prompt builder
│   ├── resources.py        # Loads LinkedIn PDF, summary, style, facts
│   ├── lambda_handler.py   # Mangum Lambda entry point
│   ├── deploy.py           # Builds lambda-deployment.zip
│   ├── requirements.txt    # pip dependencies for Lambda
│   └── data/
│       ├── facts.json      # Your personal facts (name, role, etc.)
│       ├── summary.txt     # Bio and communication style notes
│       ├── style.txt       # Tone and style guidance for the AI
│       └── linkedin.pdf    # Your LinkedIn profile export
├── frontend/
│   ├── app/
│   │   ├── page.tsx        # Home page
│   │   └── layout.tsx      # App layout
│   └── components/
│       └── twin.tsx        # Chat UI component
├── terraform/
│   ├── main.tf             # All AWS resources
│   ├── variables.tf        # Input variables
│   ├── outputs.tf          # URLs and resource names
│   ├── version.tf          # Provider versions
│   ├── backend.tf          # S3 remote state config
│   └── prod.tfvars         # Production variable overrides
├── bootstrap/
│   └── main.tf             # One-time S3 + DynamoDB state backend setup
└── scripts/
    ├── deploy.sh           # Full deploy: Lambda → Terraform → Frontend
    └── destroy.sh          # Tear down infrastructure by environment
```

---

## Persona Setup

Edit the files in `backend/data/` to personalize your twin:

**`facts.json`** — structured personal data:
```json
{
  "full_name": "James Ragive Dominique",
  "name": "Ragive",
  "current_role": "Cloud Architect & AI Engineer",
  "location": "Port-au-Prince, Haiti",
  "email": "your.email@example.com",
  "linkedin": "linkedin.com/in/yourprofile",
  "specialties": ["Cloud Architecture", "AI Engineering", "Aviation Systems"],
  "years_experience": 10
}
```

**`summary.txt`** — a free-text bio and communication style notes.

**`style.txt`** — how your twin should sound (tone, formality, personality).

**`linkedin.pdf`** — export your LinkedIn profile as a PDF and drop it here.

---

## Local Development

### Backend

```bash
cd backend
cp .env.example .env       # add your OPENAI_API_KEY
uv sync
uv run uvicorn server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Open `http://localhost:3000`.

---

## Deployment

### 1. Bootstrap (one-time)

Creates the S3 bucket and DynamoDB table for Terraform remote state:

```bash
cd bootstrap
terraform init
terraform apply
```

### 2. Set GitHub Secrets

In your repo go to **Settings → Environments** and add these secrets for each environment (`dev`, `test`, `prod`):

| Secret | Description |
|---|---|
| `AWS_ROLE_ARN` | IAM role ARN for OIDC authentication |
| `AWS_ACCOUNT_ID` | Your AWS account ID |
| `DEFAULT_AWS_REGION` | e.g. `us-east-1` |
| `OPENAI_API_KEY` | Your OpenAI API key |

### 3. Deploy via GitHub Actions

Push to `main` to trigger a `dev` deployment automatically, or use the manual workflow dispatch to target `dev`, `test`, or `prod`.

```bash
git push origin main
```

### 4. Deploy Manually

```bash
export TF_VAR_openai_api_key="sk-proj-..."
./scripts/deploy.sh dev
```

---

## Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required. Set via CI/CD secret |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model ID. Use `gpt-4o` for prod |
| `S3_BUCKET` | auto | Set by Terraform |
| `CORS_ORIGINS` | CloudFront URL | Set by Terraform |
| `USE_S3` | `true` | Enables S3 conversation memory |

Prod uses `gpt-4o` by default (set in `terraform/prod.tfvars`). Dev and test use `gpt-4o-mini`.

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) uses OIDC — no long-lived AWS credentials are stored anywhere.

```
push to main
    └── Configure AWS via OIDC
    └── Build Lambda zip (uv + deploy.py)
    └── Terraform init → workspace select → apply
    └── npm build → S3 sync
    └── CloudFront invalidation
```

The IAM role trust policy must allow:
```json
"token.actions.githubusercontent.com:sub": [
  "repo:YOUR_USERNAME/YOUR_REPO:environment:*",
  "repo:YOUR_USERNAME/YOUR_REPO:ref:refs/heads/*"
]
```

---

## Destroy Infrastructure

```bash
./scripts/destroy.sh dev
```

Or trigger the destroy workflow manually from GitHub Actions.

---

## Security Notes

- Never commit `.env` files — they are gitignored
- `OPENAI_API_KEY` is injected at runtime via `TF_VAR_openai_api_key` — it is never written to `.tfvars` or state in plaintext
- The Lambda permission uses `AllowExecutionFromAPIGateway` scoped to the specific API Gateway ARN
- CloudFront enforces TLSv1.2_2021 minimum
- All S3 memory buckets block public access

---

## License

See `LICENSE.txt`.
