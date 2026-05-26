"""Transactional email sending via Resend API."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
FROM_ADDRESS = "SoulMate <alerts@soulmate.app>"


def _build_html(deals: list[dict[str, Any]]) -> str:
    rows = ""
    for deal in deals:
        name = deal.get("name", "Unknown Shoe")
        brand = deal.get("brand", "")
        lowest_ask = deal.get("lowest_ask")
        savings = deal.get("savings")
        url = deal.get("url", "")

        price_line = f"<span style='color:#a855f7;font-size:1.1rem;font-weight:700;'>${lowest_ask:.0f}</span>" if lowest_ask else ""
        savings_line = (
            f"<span style='color:#86efac;font-size:0.85rem;margin-left:8px;'>−${savings:.2f} off retail</span>"
            if savings
            else ""
        )
        link = (
            f"<a href='{url}' style='display:inline-block;margin-top:8px;color:#a855f7;font-size:0.85rem;'>View on StockX →</a>"
            if url
            else ""
        )

        rows += f"""
        <div style='background:#1a1a1a;border-radius:10px;padding:16px 20px;margin-bottom:12px;border-left:3px solid #a855f7;'>
          <div style='font-weight:600;font-size:1rem;color:#ffffff;'>{name}</div>
          <div style='color:#9ca3af;font-size:0.8rem;margin-bottom:6px;'>{brand}</div>
          <div>{price_line}{savings_line}</div>
          {link}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style='margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;'>
  <div style='max-width:560px;margin:0 auto;padding:32px 16px;'>
    <h1 style='color:#a855f7;font-size:1.5rem;margin:0 0 4px;'>SoulMate</h1>
    <p style='color:#9ca3af;font-size:0.9rem;margin:0 0 24px;'>Price drops on your saved shoes</p>
    {rows}
    <p style='color:#4b5563;font-size:0.75rem;margin-top:24px;'>
      You're receiving this because you clicked "Email me these drops" in SoulMate.
    </p>
  </div>
</body>
</html>"""


async def send_price_drop_alert(to_email: str, deals: list[dict[str, Any]]) -> None:
    """Send a price drop alert email via Resend. No-op if RESEND_API_KEY is not set or no deals."""
    if not deals:
        return

    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key:
        logger.warning("RESEND_API_KEY not set — skipping price drop email to %s", to_email)
        return

    payload = {
        "from": FROM_ADDRESS,
        "to": [to_email],
        "subject": "Price drops on your saved shoes 👟",
        "html": _build_html(deals),
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        if resp.status_code >= 400:
            logger.error("Resend API error %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()
        else:
            logger.info("Price drop email sent to %s (%d deals)", to_email, len(deals))
