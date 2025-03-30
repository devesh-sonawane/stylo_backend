import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI()


# Data models
class GamePrice(BaseModel):
    platform: str
    price: float
    currency: str = "USD"
    url: str
    is_sale: bool = False
    sale_end_date: Optional[str] = None


class GameInfo(BaseModel):
    game_id: str
    title: str
    prices: List[GamePrice]
    lowest_price: Optional[GamePrice] = None
    last_updated: str


# In-memory cache for demo purposes
# In production, use a proper database
game_price_cache = {}


@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "game-price-comparison"}


@app.get("/api/games/search/{game_title}")
async def search_game(game_title: str):
    # TODO: Implement actual game search across platforms
    # This is a mock implementation
    mock_data = {
        "game_id": "mock_id_123",
        "title": game_title,
        "prices": [
            {
                "platform": "Steam",
                "price": 59.99,
                "currency": "USD",
                "url": f"https://store.steampowered.com/search/?term={game_title}",
                "is_sale": False,
            },
            {
                "platform": "Epic Games",
                "price": 49.99,
                "currency": "USD",
                "url": f"https://store.epicgames.com/search/{game_title}",
                "is_sale": True,
                "sale_end_date": "2024-03-01",
            },
        ],
        "last_updated": datetime.now().isoformat(),
    }

    # Find lowest price
    lowest_price = min(mock_data["prices"], key=lambda x: x["price"])
    mock_data["lowest_price"] = lowest_price

    return GameInfo(**mock_data)


@app.get("/api/games/{game_id}/prices")
async def get_game_prices(game_id: str):
    if game_id not in game_price_cache:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_price_cache[game_id]


@app.get("/api/platforms")
async def get_supported_platforms():
    return {
        "platforms": [
            {"name": "Steam", "base_url": "https://store.steampowered.com"},
            {"name": "Epic Games", "base_url": "https://store.epicgames.com"},
            {"name": "GOG", "base_url": "https://www.gog.com"},
            {"name": "PlayStation Store", "base_url": "https://store.playstation.com"},
            {"name": "Xbox Store", "base_url": "https://www.xbox.com/games"},
            {"name": "Nintendo eShop", "base_url": "https://www.nintendo.com/store"},
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
