from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models import Game, GamePrice, PriceHistory
from price_scrapers import GamePriceAggregator
from database import get_db


class PriceService:
    def __init__(self):
        self.price_aggregator = GamePriceAggregator()

    async def search_and_save_prices(
        self, game_title: str, db: Session
    ) -> Optional[Game]:
        # Search for game prices across platforms
        prices = await self.price_aggregator.get_prices(game_title)

        if not prices:
            return None

        # Create or update game record
        game = db.query(Game).filter(Game.title == game_title).first()
        if not game:
            game = Game(
                title=game_title,
                slug=game_title.lower().replace(" ", "-"),
                created_at=datetime.utcnow(),
            )
            db.add(game)
            db.flush()

        # Update prices
        for price_data in prices:
            # Save current price
            price = GamePrice(
                game_id=game.id,
                platform=price_data["platform"],
                price=price_data["price"],
                currency=price_data["currency"],
                url=price_data["url"],
                is_sale=price_data["is_sale"],
                sale_end_date=price_data.get("sale_end_date"),
                created_at=datetime.utcnow(),
            )
            db.add(price)

            # Save price history
            history = PriceHistory(
                game_id=game.id,
                platform=price_data["platform"],
                price=price_data["price"],
                currency=price_data["currency"],
                recorded_at=datetime.utcnow(),
            )
            db.add(history)

        db.commit()
        return game

    def get_price_history(
        self, game_id: int, platform: Optional[str] = None, db: Session = None
    ) -> List[PriceHistory]:
        query = db.query(PriceHistory).filter(PriceHistory.game_id == game_id)

        if platform:
            query = query.filter(PriceHistory.platform == platform)

        return query.order_by(PriceHistory.recorded_at.desc()).all()

    def get_lowest_price(self, game_id: int, db: Session) -> Optional[GamePrice]:
        return (
            db.query(GamePrice)
            .filter(GamePrice.game_id == game_id)
            .order_by(GamePrice.price.asc())
            .first()
        )

    def get_platform_prices(self, game_id: int, db: Session) -> List[GamePrice]:
        return db.query(GamePrice).filter(GamePrice.game_id == game_id).all()
