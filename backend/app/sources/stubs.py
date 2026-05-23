"""Risky source stubs.

Directly scraping Nike, Adidas, New Balance, or TikTok is ToS-violating,
fragile, and likely to break core discovery at the worst time. The legit path
is to integrate retailer product feeds, affiliate APIs, or official sneaker
data providers, then keep social signals opt-in and API-backed where possible.
"""

from collections.abc import Sequence

from app.sources.base import Shoe, ShoeSource


class ScrapeSource(ShoeSource):
    def list_shoes(self) -> Sequence[Shoe]:
        raise NotImplementedError("Use product feeds or affiliate APIs instead.")


class SocialSource(ShoeSource):
    def list_shoes(self) -> Sequence[Shoe]:
        raise NotImplementedError("Use official or approved social APIs instead.")
