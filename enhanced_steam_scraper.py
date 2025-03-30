import os
import requests
import time
import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from steam.webapi import WebAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable or use fallback
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "8F3C865FCFC0FC9D344A7B55569FBC6B")

# Common game variations and their app IDs
POPULAR_GAMES = {
    "counter strike global offensive": 730,
    "csgo": 730,
    "cs go": 730,
    "cs:go": 730,
    # Add more popular games as needed
}

# Terms to exclude from search results
EXCLUDED_TERMS = [
    "skin",
    "soundtrack",
    "dlc",
    "trailer",
    "demo",
    "server",
    "dedicated",
    "test",
]


def normalize_game_name(name):
    """Normalize game name by removing special characters and extra spaces"""
    name = name.lower()
    name = name.replace(":", "")
    name = name.replace("-", " ")
    return " ".join(name.split())


def is_valid_app_id(app_id_str):
    """Check if a string is a valid Steam app ID"""
    try:
        app_id = int(app_id_str)
        return app_id > 0
    except ValueError:
        return False


def get_game_details_sync(appid):
    """Get game details from Steam API (synchronous version)"""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
    try:
        response = requests.get(url)
        if response.status_code == 429:  # Rate limit hit
            print("Rate limit reached. Waiting before retrying...")
            time.sleep(5)  # Wait 5 seconds before retrying
            response = requests.get(url)

        if response.status_code == 200:
            try:
                data = response.json()
                if not data or str(appid) not in data:
                    return None

                app_data = data[str(appid)]
                if not app_data.get("success"):
                    return None

                game_data = app_data["data"]
                if not game_data:
                    return None

                if "price_overview" in game_data:
                    price_info = game_data["price_overview"]
                    return {
                        "name": game_data.get("name", ""),
                        "price": price_info.get("final_formatted", "N/A"),
                        "discount": price_info.get("discount_percent", 0),
                        "initial_price": (
                            price_info.get("initial_formatted")
                            if price_info.get("discount_percent", 0) > 0
                            else None
                        ),
                        "price_numeric": price_info.get("final", 0) / 100,
                        "initial_price_numeric": price_info.get("initial", 0) / 100,
                        "currency": price_info.get("currency", "USD"),
                        "platforms": game_data.get("platforms", {}),
                        "genres": [
                            genre.get("description", "")
                            for genre in game_data.get("genres", [])
                        ],
                        "categories": [
                            cat.get("description", "")
                            for cat in game_data.get("categories", [])
                        ],
                        "url": f"https://store.steampowered.com/app/{appid}",
                    }
                elif game_data.get("is_free", False):
                    return {
                        "name": game_data.get("name", ""),
                        "price": "Free to Play",
                        "discount": 0,
                        "initial_price": None,
                        "price_numeric": 0,
                        "initial_price_numeric": 0,
                        "currency": "USD",
                        "platforms": game_data.get("platforms", {}),
                        "genres": [
                            genre.get("description", "")
                            for genre in game_data.get("genres", [])
                        ],
                        "categories": [
                            cat.get("description", "")
                            for cat in game_data.get("categories", [])
                        ],
                        "url": f"https://store.steampowered.com/app/{appid}",
                    }
                else:
                    return None
            except ValueError:
                return None
        else:
            return None
    except Exception:
        return None


async def get_game_details_async(appid, session):
    """Get game details from Steam API (asynchronous version)"""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
    try:
        async with session.get(url) as response:
            if response.status == 429:  # Rate limit hit
                await asyncio.sleep(5)  # Wait 5 seconds before retrying
                async with session.get(url) as retry_response:
                    response = retry_response

            if response.status == 200:
                try:
                    data = await response.json()
                    if not data or str(appid) not in data:
                        return None

                    app_data = data[str(appid)]
                    if not app_data.get("success"):
                        return None

                    game_data = app_data["data"]
                    if not game_data:
                        return None

                    if "price_overview" in game_data:
                        price_info = game_data["price_overview"]
                        return {
                            "name": game_data.get("name", ""),
                            "price": price_info.get("final_formatted", "N/A"),
                            "discount": price_info.get("discount_percent", 0),
                            "initial_price": (
                                price_info.get("initial_formatted")
                                if price_info.get("discount_percent", 0) > 0
                                else None
                            ),
                            "price_numeric": price_info.get("final", 0) / 100,
                            "initial_price_numeric": price_info.get("initial", 0) / 100,
                            "currency": price_info.get("currency", "USD"),
                            "platforms": game_data.get("platforms", {}),
                            "genres": [
                                genre.get("description", "")
                                for genre in game_data.get("genres", [])
                            ],
                            "categories": [
                                cat.get("description", "")
                                for cat in game_data.get("categories", [])
                            ],
                            "url": f"https://store.steampowered.com/app/{appid}",
                        }
                    elif game_data.get("is_free", False):
                        return {
                            "name": game_data.get("name", ""),
                            "price": "Free to Play",
                            "discount": 0,
                            "initial_price": None,
                            "price_numeric": 0,
                            "initial_price_numeric": 0,
                            "currency": "USD",
                            "platforms": game_data.get("platforms", {}),
                            "genres": [
                                genre.get("description", "")
                                for genre in game_data.get("genres", [])
                            ],
                            "categories": [
                                cat.get("description", "")
                                for cat in game_data.get("categories", [])
                            ],
                            "url": f"https://store.steampowered.com/app/{appid}",
                        }
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None
    except Exception:
        return None


class EnhancedSteamScraper:
    """Enhanced Steam scraper that combines the functionality of teststeamapi.py and SteamScraper"""

    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.api_key = STEAM_API_KEY
        self.api = WebAPI(key=self.api_key)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_game(self, title: str) -> Optional[Dict]:
        """Search for a game on Steam and return its details"""
        print(f"Searching for game: {title}")

        # Check if input is an app ID
        if is_valid_app_id(title):
            app_id = int(title)
            details = await get_game_details_async(app_id, self.session)
            if details:
                return {
                    "platform": "Steam",
                    "title": details["name"],
                    "price": details["price_numeric"],
                    "initial_price": details["initial_price_numeric"],
                    "currency": details["currency"],
                    "discount_percent": details["discount"],
                    "url": details["url"],
                    "is_sale": details["discount"] > 0,
                    "platforms": details["platforms"],
                    "genres": details["genres"],
                    "categories": details["categories"],
                }
            return None

        # If not an app ID, check for popular games first
        normalized_search = normalize_game_name(title)
        if normalized_search in POPULAR_GAMES:
            app_id = POPULAR_GAMES[normalized_search]
            details = await get_game_details_async(app_id, self.session)
            if details:
                return {
                    "platform": "Steam",
                    "title": details["name"],
                    "price": details["price_numeric"],
                    "initial_price": details["initial_price_numeric"],
                    "currency": details["currency"],
                    "discount_percent": details["discount"],
                    "url": details["url"],
                    "is_sale": details["discount"] > 0,
                    "platforms": details["platforms"],
                    "genres": details["genres"],
                    "categories": details["categories"],
                }

        # Try the standard search method first
        search_url = f"https://store.steampowered.com/api/storesearch/?term={title}&l=english&cc=US"
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("items"):
                        game = data["items"][0]
                        app_id = game["id"]

                        # Get current price info
                        store_api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=US&filters=price_overview,platforms,genres,categories"
                        async with self.session.get(store_api_url) as store_response:
                            if store_response.status == 200:
                                store_data = await store_response.json()
                                app_data = store_data.get(str(app_id), {})
                                if not app_data.get("success"):
                                    return None

                                data = app_data.get("data", {})
                                price_data = data.get("price_overview", {})

                                return {
                                    "platform": "Steam",
                                    "title": game["name"],
                                    "price": price_data.get("final", 0) / 100,
                                    "initial_price": price_data.get("initial", 0) / 100,
                                    "currency": price_data.get("currency", "USD"),
                                    "discount_percent": price_data.get(
                                        "discount_percent", 0
                                    ),
                                    "url": f"https://store.steampowered.com/app/{app_id}",
                                    "is_sale": price_data.get("discount_percent", 0)
                                    > 0,
                                    "platforms": data.get("platforms", {}),
                                    "genres": [
                                        genre.get("description")
                                        for genre in data.get("genres", [])
                                    ],
                                    "categories": [
                                        cat.get("description")
                                        for cat in data.get("categories", [])
                                    ],
                                }
        except Exception as e:
            print(f"Error in standard search: {e}")

        # If standard search fails, try the advanced search with the Steam Web API
        try:
            # Get app list with retry mechanism
            max_retries = 3
            apps = None
            for attempt in range(max_retries):
                try:
                    apps = self.api.ISteamApps.GetAppList()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                    else:
                        print(
                            f"Failed to get app list after {max_retries} attempts: {e}"
                        )
                        return None

            if not apps:
                return None

            # First try exact match with normalized names
            results = [
                app
                for app in apps["applist"]["apps"]
                if normalized_search == normalize_game_name(app["name"])
                and not any(term in app["name"].lower() for term in EXCLUDED_TERMS)
            ]

            # If no exact matches, try contains match but exclude non-game items
            if not results:
                results = [
                    app
                    for app in apps["applist"]["apps"]
                    if normalized_search in normalize_game_name(app["name"])
                    and not any(term in app["name"].lower() for term in EXCLUDED_TERMS)
                ]

            if not results:
                return None

            # Get details for the first result
            details = await get_game_details_async(results[0]["appid"], self.session)
            if details:
                return {
                    "platform": "Steam",
                    "title": details["name"],
                    "price": details["price_numeric"],
                    "initial_price": details["initial_price_numeric"],
                    "currency": details["currency"],
                    "discount_percent": details["discount"],
                    "url": details["url"],
                    "is_sale": details["discount"] > 0,
                    "platforms": details["platforms"],
                    "genres": details["genres"],
                    "categories": details["categories"],
                }

        except Exception as e:
            print(f"Error in advanced search: {e}")

        return None

    async def search_multiple_games(self, title: str, limit: int = 10) -> List[Dict]:
        """Search for multiple games matching the title and return their details"""
        normalized_search = normalize_game_name(title)
        results = []

        try:
            # Get app list with retry mechanism
            max_retries = 3
            apps = None
            for attempt in range(max_retries):
                try:
                    apps = self.api.ISteamApps.GetAppList()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                    else:
                        print(
                            f"Failed to get app list after {max_retries} attempts: {e}"
                        )
                        return []

            if not apps:
                return []

            # First try exact match with normalized names
            matched_apps = [
                app
                for app in apps["applist"]["apps"]
                if normalized_search == normalize_game_name(app["name"])
                and not any(term in app["name"].lower() for term in EXCLUDED_TERMS)
            ]

            # If no exact matches, try contains match but exclude non-game items
            if not matched_apps:
                matched_apps = [
                    app
                    for app in apps["applist"]["apps"]
                    if normalized_search in normalize_game_name(app["name"])
                    and not any(term in app["name"].lower() for term in EXCLUDED_TERMS)
                ]

            if not matched_apps:
                return []

            # Get details for up to 'limit' results
            tasks = []
            for app in matched_apps[:limit]:
                tasks.append(get_game_details_async(app["appid"], self.session))

            details_list = await asyncio.gather(*tasks)
            for details in details_list:
                if details:
                    results.append(
                        {
                            "platform": "Steam",
                            "title": details["name"],
                            "price": details["price_numeric"],
                            "initial_price": details["initial_price_numeric"],
                            "currency": details["currency"],
                            "discount_percent": details["discount"],
                            "url": details["url"],
                            "is_sale": details["discount"] > 0,
                            "platforms": details["platforms"],
                            "genres": details["genres"],
                            "categories": details["categories"],
                        }
                    )

        except Exception as e:
            print(f"Error searching multiple games: {e}")

        return results


# Example usage:
# async def main():
#     async with EnhancedSteamScraper() as scraper:
#         # Search for a single game
#         result = await scraper.search_game("Cyberpunk 2077")
#         print(result)
#
#         # Search for multiple games
#         results = await scraper.search_multiple_games("fallout", limit=5)
#         for game in results:
#             print(f"{game['title']}: {game['price']} {game['currency']}")
#
# if __name__ == "__main__":
#     asyncio.run(main())
