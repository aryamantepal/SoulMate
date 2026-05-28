"""Derive a named style persona from a taste vector.

Each dimension anchors an archetype. We pick the persona whose dimension the
user leans into most strongly. If the taste vector is still near-zero (few
swipes), we return the cold-start "Fresh Explorer" persona.
"""

from __future__ import annotations

from app.taste.dims import DIMENSIONS, TasteVec

# dim -> (name, emoji, blurb)
_PERSONA_BY_DIM: dict[str, tuple[str, str, str]] = {
    "chunk": ("Chunk Lord", "🦾", "Bigger is better. You gravitate to bold, oversized silhouettes."),
    "retro": ("Retro Hunter", "📼", "You chase the classics — heritage silhouettes and throwback colorways."),
    "warm": ("Warm Tones", "🔥", "Earth-warm palettes: rust, tan, cream. Cozy over clinical."),
    "minimal": ("Clean Minimalist", "🤍", "Less is more. Quiet design, crisp lines, no noise."),
    "earthy": ("Gorpcore Explorer", "🏔️", "Trail-ready and outdoorsy. Function meets muted, natural tones."),
    "loud": ("Loud & Proud", "⚡", "Statement pairs. Bright, bold, impossible to ignore."),
    "techy": ("Tech Head", "🛰️", "Future-forward materials and engineered, performance-driven design."),
}

_FRESH = ("Fresh Explorer", "🧭", "Still mapping your taste. Keep swiping to unlock your style persona.")

# Below this norm the signal is too weak to call a persona.
_MIN_NORM = 0.25


def _norm(taste: TasteVec) -> float:
    return sum(taste.get(dim, 0.0) ** 2 for dim in DIMENSIONS) ** 0.5


def derive_persona(taste: TasteVec) -> dict[str, str]:
    """Return {name, emoji, blurb, dim} for the strongest taste dimension."""
    if _norm(taste) < _MIN_NORM:
        name, emoji, blurb = _FRESH
        return {"name": name, "emoji": emoji, "blurb": blurb, "dim": ""}

    top_dim = max(DIMENSIONS, key=lambda dim: taste.get(dim, 0.0))
    if taste.get(top_dim, 0.0) <= 0:
        name, emoji, blurb = _FRESH
        return {"name": name, "emoji": emoji, "blurb": blurb, "dim": ""}

    name, emoji, blurb = _PERSONA_BY_DIM[top_dim]
    return {"name": name, "emoji": emoji, "blurb": blurb, "dim": top_dim}
