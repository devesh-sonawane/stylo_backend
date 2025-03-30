import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from price_scrapers import SteamScraper

# Load .env from the gameai directory
env_path = Path("../gameai/.env")
print(f"Loading .env from: {env_path.absolute()}")
load_dotenv(dotenv_path=env_path)

steam_key = os.getenv("STEAM_API_KEY")
print(f"Steam API Key loaded: {steam_key}")


async def test_steam_scraper():
    print("Initializing Steam scraper...")
    async with SteamScraper() as scraper:
        print("Testing with game: Elden Ring")
        result = await scraper.search_game("Elden Ring")
        print("Search result:", result)


if __name__ == "__main__":
    asyncio.run(test_steam_scraper())
