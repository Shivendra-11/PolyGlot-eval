# I4 Polyglot Pair — proof artifact

## Terminal 1 — FastAPI service

```bash
cd service
pip install -r requirements.txt
pytest -q
uvicorn main:app --reload --port 8000
```

## Terminal 2 — Node CLI

```bash
cd client
node index.js 100 USD EUR
bash test_client.sh
```

## Endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /convert` → `{ "amount", "from", "to", "converted", "rate" }`

Hardcoded rates: USD, EUR, GBP, JPY, INR, AUD, CAD.
