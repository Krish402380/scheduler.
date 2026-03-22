"""
FastAPI application entry point for the knowledge retention backend.
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.decay import LambdaConfig, compute_decay

app = FastAPI(
    title="Knowledge Retention API",
    description=(
        "Backend service that computes live decay scores for tracked topics "
        "using an exponential decay model."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class DecayRequest(BaseModel):
    """Payload for computing a decay score."""

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence rating from the most recent session (0.0–1.0).",
    )
    last_session_date: datetime = Field(
        ...,
        description="ISO-8601 datetime of the most recent study session.",
    )
    lambda_low: float = Field(
        default=0.3,
        gt=0.0,
        description="Decay constant for low-confidence topics.",
    )
    lambda_mid: float = Field(
        default=0.15,
        gt=0.0,
        description="Decay constant for medium-confidence topics.",
    )
    lambda_high: float = Field(
        default=0.07,
        gt=0.0,
        description="Decay constant for high-confidence topics.",
    )


class DecayResponse(BaseModel):
    """Computed retention score."""

    retention_score: float = Field(
        ...,
        description="Estimated retention percentage (0.0–100.0).",
    )
    days_elapsed: float = Field(
        ...,
        description="Number of days since the last session.",
    )
    confidence: float
    last_session_date: datetime


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", tags=["health"])
def health_check():
    """Simple liveness probe."""
    return {"status": "ok", "service": "knowledge-retention-api"}


@app.post("/decay", response_model=DecayResponse, tags=["decay"])
def get_decay_score(payload: DecayRequest):
    """
    Compute the current retention score for a topic.

    Accepts the last session's confidence rating and date, applies the
    exponential decay formula, and returns the estimated retention percentage.
    """
    try:
        config = LambdaConfig(
            lambda_low=payload.lambda_low,
            lambda_mid=payload.lambda_mid,
            lambda_high=payload.lambda_high,
        )
        result = compute_decay(
            confidence=payload.confidence,
            last_session_date=payload.last_session_date,
            config=config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DecayResponse(
        retention_score=result.retention_score,
        days_elapsed=result.days_elapsed,
        confidence=payload.confidence,
        last_session_date=payload.last_session_date,
    )
