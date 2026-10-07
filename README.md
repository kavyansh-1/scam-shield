# Scam Shield

Real-time scam co-pilot for India: detects digital-arrest, fake-KYC, UPI-collect and
remote-access fraud in Hindi, English and Hinglish from pasted text, screenshots or a
live call transcript. Warns visually and by voice, alerts a Telegram "guardian" (with
escalation), generates a complaint-evidence PDF for 1930 / cybercrime.gov.in, and has a
practice mode where an AI plays the scammer.

**Status:** scaffold + contract only. No features yet. See `docs/CONTRACT.md`.

## Run (local)
```bash
cp .env.example .env            # LLM_PROVIDER=mock works with no keys

# backend  -> http://localhost:8000/api/health
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend -> http://localhost:3000
cd frontend && npm install && npm run dev
```

## Run (Docker)
```bash
docker compose up --build
```

## Layout
`backend/` FastAPI · `frontend/` Next.js 14 · `docs/` contract & design · `eval/` detection eval ·
`demo/` scripted calls · `scripts/` smoke tests.

## Notes
- `LLM_MODEL` is user-set; no model names are hardcoded.
- Telegram runs in mock mode when `TELEGRAM_BOT_TOKEN` / `TELEGRAM_BOT_USERNAME` are empty.
- Est. money saved uses `AVG_LOSS_PREVENTED_INR` and must be labelled an estimate in the UI.
