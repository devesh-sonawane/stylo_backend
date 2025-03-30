from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    slug = Column(String, unique=True)
    description = Column(String)
    image_url = Column(String)
    release_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prices = relationship("GamePrice", back_populates="game")


class GamePrice(Base):
    __tablename__ = "game_prices"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    platform = Column(String)
    price = Column(Float)
    currency = Column(String, default="USD")
    url = Column(String)
    is_sale = Column(Boolean, default=False)
    sale_end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="prices")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    platform = Column(String)
    price = Column(Float)
    currency = Column(String)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game")


def init_db(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine
