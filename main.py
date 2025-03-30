import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from database import get_db, init_db
from models import Game, GamePrice, PriceHistory
from price_service import PriceService
from game_agent import GameAgent
from pydantic import BaseModel, Field

app = FastAPI(
    title="Gaming AI API",
    description="API for game recommendations, chat, and price comparison",
)
price_service = PriceService()

# Initialize game agent
game_agent = GameAgent()

# Initialize database
init_db()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Pydantic models for API
class PriceResponse(BaseModel):
    platform: str
    price: float
    currency: str
    url: str
    is_sale: bool
    sale_end_date: Optional[str] = None


class GameResponse(BaseModel):
    id: int
    title: str
    prices: List[PriceResponse]
    lowest_price: Optional[PriceResponse]
    last_updated: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class GameSearchRequest(BaseModel):
    query: str
    limit: int = 5


class GameRecommendationRequest(BaseModel):
    preferences: str
    limit: int = 5


class GameSearchResult(BaseModel):
    id: str
    title: str
    description: str
    genres: str
    price: str
    release_date: str
    developers: str
    publishers: str
    platforms: str
    metacritic_score: float = 0
    image_url: str = ""
    website: str = ""
    relevance_score: float


@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "gaming-ai-service"}


@app.get("/api/games/search/{game_title}", response_model=GameResponse)
async def search_game(game_title: str, db: Session = Depends(get_db)):
    game = await price_service.search_and_save_prices(game_title, db)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    prices = price_service.get_platform_prices(game.id, db)
    lowest_price = price_service.get_lowest_price(game.id, db)

    return {
        "id": game.id,
        "title": game.title,
        "prices": [
            {
                "platform": p.platform,
                "price": p.price,
                "currency": p.currency,
                "url": p.url,
                "is_sale": p.is_sale,
                "sale_end_date": (
                    p.sale_end_date.isoformat() if p.sale_end_date else None
                ),
            }
            for p in prices
        ],
        "lowest_price": (
            {
                "platform": lowest_price.platform,
                "price": lowest_price.price,
                "currency": lowest_price.currency,
                "url": lowest_price.url,
                "is_sale": lowest_price.is_sale,
                "sale_end_date": (
                    lowest_price.sale_end_date.isoformat()
                    if lowest_price.sale_end_date
                    else None
                ),
            }
            if lowest_price
            else None
        ),
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.get("/api/games/{game_id}/history")
async def get_price_history(
    game_id: int, platform: Optional[str] = None, db: Session = Depends(get_db)
):
    history = price_service.get_price_history(game_id, platform, db)
    return {
        "history": [
            {
                "platform": h.platform,
                "price": h.price,
                "currency": h.currency,
                "recorded_at": h.recorded_at.isoformat(),
            }
            for h in history
        ]
    }


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


# AI Agent endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return a response with session information"""
    try:
        result = await game_agent.chat(request.message, request.session_id)
        return {"response": result["response"], "session_id": result["session_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.post("/api/games/ai-search", response_model=List[GameSearchResult])
async def ai_search_games(request: GameSearchRequest):
    """Search for games using AI"""
    try:
        results = await game_agent.search_games(request.query, request.limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching games: {str(e)}")


@app.post("/api/games/recommend", response_model=List[GameSearchResult])
async def recommend_games(request: GameRecommendationRequest):
    """Get game recommendations based on preferences"""
    try:
        results = await game_agent.recommend_games(request.preferences, request.limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting recommendations: {str(e)}"
        )


# Session management
@app.get("/api/session/status")
async def get_session_status(request: Request):
    """Get the status of the current session"""
    return {
        "session_id": request.session.get("session_id", None),
        "is_active": game_agent.vectorstore is not None,
        "embeddings_available": os.path.exists(game_agent.db_directory),
        "active_sessions": len(game_agent.sessions),
    }


class ResetSessionRequest(BaseModel):
    session_id: str


class ResetSessionResponse(BaseModel):
    success: bool
    session_id: str


@app.post("/api/reset", response_model=ResetSessionResponse)
async def reset_session(request: ResetSessionRequest):
    """Reset a conversation session"""
    session_id = request.session_id

    # Remove the session if it exists
    if session_id in game_agent.sessions:
        del game_agent.sessions[session_id]

    # Create a new session
    session_info = game_agent._get_or_create_session(session_id)

    return {"success": True, "session_id": session_info["session_id"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
