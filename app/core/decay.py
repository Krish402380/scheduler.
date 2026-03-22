"""
Core exponential decay logic for knowledge retention scoring.

Formula: retention = confidence_weight * e^(-lambda * days_elapsed)

- confidence_weight: baseline retention derived from the last session's
  confidence rating (0.0–1.0 scale, mapped to 0–100).
- lambda: decay constant that controls how fast retention drops.
  Higher lambda → faster decay. Scales inversely with confidence so
  that poorly-understood topics fade more quickly.
- days_elapsed: number of days since the last study session.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NamedTuple


# Default lambda constants per confidence band.
# These match the UserSettings defaults in the Prisma schema.
DEFAULT_LAMBDA_LOW: float = 0.3   # confidence in [0.0, 0.4)
DEFAULT_LAMBDA_MID: float = 0.15  # confidence in [0.4, 0.7]
DEFAULT_LAMBDA_HIGH: float = 0.07 # confidence in (0.7, 1.0]


@dataclass
class LambdaConfig:
    """Decay constants (λ) for each confidence band."""
    lambda_low: float = DEFAULT_LAMBDA_LOW
    lambda_mid: float = DEFAULT_LAMBDA_MID
    lambda_high: float = DEFAULT_LAMBDA_HIGH


class DecayResult(NamedTuple):
    """Result of a decay computation."""
    retention_score: float  # 0.0–100.0
    days_elapsed: float


def _pick_lambda(confidence: float, config: LambdaConfig) -> float:
    """Return the appropriate λ value for a given confidence rating.

    Confidence bands (inclusive lower, exclusive upper except at 1.0):
    - [0.0, 0.4)  → lambda_low   (weak understanding, fast decay)
    - [0.4, 0.7]  → lambda_mid   (moderate understanding)
    - (0.7, 1.0]  → lambda_high  (strong understanding, slow decay)
    """
    if confidence < 0.4:
        return config.lambda_low
    if confidence <= 0.7:
        return config.lambda_mid
    return config.lambda_high


def _days_since(last_session_date: datetime, now: datetime) -> float:
    """Return the number of days elapsed between *last_session_date* and *now*."""
    if last_session_date.tzinfo is not None:
        ref = last_session_date
    else:
        ref = last_session_date.replace(tzinfo=timezone.utc)

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    return max((now - ref).total_seconds() / 86_400, 0.0)


def compute_decay(
    confidence: float,
    last_session_date: datetime,
    *,
    config: LambdaConfig | None = None,
    now: datetime | None = None,
) -> DecayResult:
    """
    Compute the current retention score for a topic.

    Parameters
    ----------
    confidence:
        The confidence rating recorded in the most recent session (0.0–1.0).
    last_session_date:
        Timezone-aware (or naive UTC) datetime of the most recent session.
    config:
        Optional :class:`LambdaConfig` with custom decay constants.
        Defaults to :data:`DEFAULT_LAMBDA_*` values.
    now:
        Override the current time (useful for testing). Defaults to
        ``datetime.now(timezone.utc)``.

    Returns
    -------
    DecayResult
        Named tuple with ``retention_score`` (0.0–100.0) and
        ``days_elapsed`` (float).

    Raises
    ------
    ValueError
        If ``confidence`` is outside the range ``[0.0, 1.0]``.
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            f"confidence must be between 0.0 and 1.0, got {confidence!r}"
        )

    if config is None:
        config = LambdaConfig()

    if now is None:
        now = datetime.now(timezone.utc)

    days_elapsed = _days_since(last_session_date, now)
    lam = _pick_lambda(confidence, config)
    confidence_weight = confidence * 100.0
    retention = confidence_weight * math.exp(-lam * days_elapsed)
    score = round(min(max(retention, 0.0), 100.0), 4)
    return DecayResult(retention_score=score, days_elapsed=round(days_elapsed, 4))
