"""Compute taste-evolution stats from a user's swipe timeline."""

from __future__ import annotations

from typing import Any

from app.taste.dims import DIMENSIONS, TasteVec


def _downsample(rows: list[dict[str, Any]], points: int = 12) -> list[dict[str, Any]]:
    if len(rows) <= points:
        return rows
    step = len(rows) / points
    return [rows[min(int(i * step), len(rows) - 1)] for i in range(points)]


def compute_stats(timeline: list[dict[str, Any]], taste: TasteVec) -> dict[str, Any]:
    """Build a stats payload from the (oldest-first) swipe timeline + current taste.

    Returns counts, like ratio, the strongest dimensions, and a downsampled
    trajectory of the dominant dimension's value over time (for a sparkline).
    """
    total = len(timeline)
    likes = sum(1 for row in timeline if row["direction"] == 1)
    passes = total - likes
    like_ratio = round(likes / total, 2) if total else 0.0

    # Strongest dims by absolute value, sorted descending.
    top_dims = sorted(
        ((dim, taste.get(dim, 0.0)) for dim in DIMENSIONS),
        key=lambda kv: abs(kv[1]),
        reverse=True,
    )[:3]

    dominant = top_dims[0][0] if top_dims and abs(top_dims[0][1]) > 0 else None
    trajectory: list[float] = []
    if dominant:
        sampled = _downsample(timeline)
        trajectory = [round(float(row["taste_after"].get(dominant, 0.0)), 3) for row in sampled]

    return {
        "total": total,
        "likes": likes,
        "passes": passes,
        "like_ratio": like_ratio,
        "top_dims": [{"dim": dim, "value": round(val, 3)} for dim, val in top_dims],
        "dominant_dim": dominant,
        "trajectory": trajectory,
    }
