from app.sources.base import Shoe, ShoeSource
from app.sources.seed import CATALOG


class MockSource(ShoeSource):
    def list_shoes(self) -> list[Shoe]:
        return list(CATALOG)

    def get_shoe(self, shoe_id: str) -> Shoe | None:
        return next((shoe for shoe in CATALOG if shoe.id == shoe_id), None)
