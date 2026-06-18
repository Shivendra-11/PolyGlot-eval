"""FastAPI currency converter — proof artifact for polyglot-eval I4."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.5,
    "INR": 83.1,
    "AUD": 1.52,
    "CAD": 1.36,
}

app = FastAPI(title="polyglot-eval convert")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConvertRequest(BaseModel):
    amount: float = Field(gt=0)
    from_currency: str = Field(alias="from")
    to_currency: str = Field(alias="to")

    model_config = {"populate_by_name": True}


class ConvertResponse(BaseModel):
    amount: float
    from_currency: str = Field(alias="from")
    to_currency: str = Field(alias="to")
    converted: float
    rate: float

    model_config = {"populate_by_name": True}


def _convert(amount: float, src: str, dst: str) -> tuple[float, float]:
    src_u, dst_u = src.upper(), dst.upper()
    if src_u not in RATES or dst_u not in RATES:
        raise HTTPException(status_code=422, detail="unknown currency")
    usd = amount / RATES[src_u]
    converted = usd * RATES[dst_u]
    rate = RATES[dst_u] / RATES[src_u]
    return round(converted, 4), round(rate, 6)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/convert", response_model=ConvertResponse)
def convert(body: ConvertRequest) -> ConvertResponse:
    converted, rate = _convert(body.amount, body.from_currency, body.to_currency)
    return ConvertResponse(
        amount=body.amount,
        from_currency=body.from_currency.upper(),
        to_currency=body.to_currency.upper(),
        converted=converted,
        rate=rate,
    )
