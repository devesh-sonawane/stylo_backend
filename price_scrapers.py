import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime


class PriceScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


class SteamScraper(PriceScraper):
    def __init__(self):
        super().__init__()
        from dotenv import load_dotenv
        import os
        from enhanced_steam_scraper import (
            EnhancedSteamScraper,
            normalize_game_name,
            is_valid_app_id,
        )

        load_dotenv()
        self.api_key = os.getenv(
            "STEAM_API_KEY"
        )  # Get API key from environment variable
        self.enhanced_scraper = None
        self.normalize_game_name = normalize_game_name
        self.is_valid_app_id = is_valid_app_id

    async def search_game(self, title: str) -> Optional[Dict]:
        print(f"Searching for game: {title}")

        # Initialize enhanced scraper if not already done
        if self.enhanced_scraper is None:
            from enhanced_steam_scraper import EnhancedSteamScraper

            self.enhanced_scraper = EnhancedSteamScraper()
            self.enhanced_scraper.session = self.session

        try:
            # Use the enhanced scraper to search for the game
            result = await self.enhanced_scraper.search_game(title)
            if result:
                return result

            # Fallback to original implementation if enhanced scraper fails
            search_url = f"https://store.steampowered.com/api/storesearch/?term={title}&l=english&cc=US"
            print(f"Using Steam API key: {self.api_key}")
            print(f"Search URL: {search_url}")

            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data.get("items"):
                        print(f"No items found for {title}")
                        return None
                    print(f"Found {len(data['items'])} results for {title}")

                    game = data["items"][0]
                    app_id = game["id"]

                    # Get detailed app info using Steam Web API
                    if self.api_key:
                        details_url = f"https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={self.api_key}&appid={app_id}"
                        async with self.session.get(details_url) as details_response:
                            if details_response.status == 200:
                                details_data = await details_response.json()

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
                                "price": price_data.get("final", 0)
                                / 100,  # Convert cents to dollars
                                "initial_price": price_data.get("initial", 0) / 100,
                                "currency": price_data.get("currency", "USD"),
                                "discount_percent": price_data.get(
                                    "discount_percent", 0
                                ),
                                "url": f"https://store.steampowered.com/app/{app_id}",
                                "is_sale": price_data.get("discount_percent", 0) > 0,
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
            print(f"Error fetching Steam data: {e}")
            print(f"Full error details: {str(e.__class__.__name__)}: {str(e)}")

        return None

    async def search_multiple_games(self, title: str, limit: int = 10) -> List[Dict]:
        """Search for multiple games matching the title and return their details"""
        # Initialize enhanced scraper if not already done
        if self.enhanced_scraper is None:
            from enhanced_steam_scraper import EnhancedSteamScraper

            self.enhanced_scraper = EnhancedSteamScraper()
            self.enhanced_scraper.session = self.session

        try:
            # Use the enhanced scraper to search for multiple games
            results = await self.enhanced_scraper.search_multiple_games(title, limit)
            return results
        except Exception as e:
            print(f"Error searching multiple games: {e}")
            return []


class EpicGamesScraper(PriceScraper):
    async def search_game(self, title: str) -> Optional[Dict]:
        # Note: Epic Games requires GraphQL API calls
        # This is a simplified mock implementation
        search_url = f"https://store.epicgames.com/graphql"
        try:
            query = {
                "query": """
                query searchStoreQuery($searchString: String!) {
                    Catalog {
                        searchStore(keywords: $searchString) {
                            elements {
                                title
                                price {
                                    totalPrice {
                                        discountPrice
                                        originalPrice
                                    }
                                }
                                catalogNs {
                                    mappings(pageType: "productHome") {
                                        pageSlug
                                    }
                                }
                            }
                        }
                    }
                }
                """,
                "variables": {"searchString": title},
            }

            # Mock response for demonstration
            return {
                "platform": "Epic Games",
                "title": title,
                "price": 59.99,
                "currency": "USD",
                "url": f"https://store.epicgames.com/search/{title}",
                "is_sale": False,
            }
        except Exception as e:
            print(f"Error scraping Epic Games: {e}")
        return None


class GOGScraper(PriceScraper):
    async def search_game(self, title: str) -> Optional[Dict]:
        search_url = (
            f"https://www.gog.com/games/ajax/filtered?mediaType=game&search={title}"
        )
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["products"]:
                        game = data["products"][0]
                        return {
                            "platform": "GOG",
                            "title": game["title"],
                            "price": game["price"]["amount"],
                            "currency": game["price"]["currency"],
                            "url": f'https://www.gog.com{game["url"]}',
                            "is_sale": game["price"]["isDiscounted"],
                        }
        except Exception as e:
            print(f"Error scraping GOG: {e}")
        return None


class PlayStationStoreScraper(PriceScraper):
    async def search_game(self, title: str) -> Optional[Dict]:
        search_url = (
            f"https://store.playstation.com/api/v1/search/games?q={title}&region=US"
        )
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("games", []):
                        game = data["games"][0]
                        return {
                            "platform": "PlayStation Store",
                            "title": game["name"],
                            "price": float(game.get("price", {}).get("basePrice", 0)),
                            "currency": "USD",
                            "url": f'https://store.playstation.com/product/{game["id"]}',
                            "is_sale": game.get("price", {}).get("discountedPrice", 0)
                            < game.get("price", {}).get("basePrice", 0),
                        }
        except Exception as e:
            print(f"Error scraping PlayStation Store: {e}")
        return None


class XboxStoreScraper(PriceScraper):
    async def search_game(self, title: str) -> Optional[Dict]:
        search_url = f"https://xbox-store-api.com/api/games/search?q={title}&market=US"
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("products", []):
                        game = data["products"][0]
                        return {
                            "platform": "Xbox Store",
                            "title": game["title"],
                            "price": float(game.get("price", 0)),
                            "currency": "USD",
                            "url": f'https://www.xbox.com/games/store/{game["id"]}',
                            "is_sale": game.get("isOnSale", False),
                        }
        except Exception as e:
            print(f"Error scraping Xbox Store: {e}")
        return None


class NintendoShopScraper(PriceScraper):
    async def search_game(self, title: str) -> Optional[Dict]:
        search_url = f"https://api.ec.nintendo.com/v1/search?q={title}&country=US"
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("games", []):
                        game = data["games"][0]
                        return {
                            "platform": "Nintendo eShop",
                            "title": game["title"],
                            "price": float(
                                game.get("price", {}).get("regular_price", 0)
                            ),
                            "currency": "USD",
                            "url": f'https://www.nintendo.com/store/products/{game["id"]}',
                            "is_sale": game.get("price", {}).get("discount_price", 0)
                            < game.get("price", {}).get("regular_price", 0),
                        }
        except Exception as e:
            print(f"Error scraping Nintendo eShop: {e}")
        return None


class GamePriceAggregator:
    def __init__(self):
        self.scrapers = [
            SteamScraper(),
            EpicGamesScraper(),
            GOGScraper(),
            PlayStationStoreScraper(),
            XboxStoreScraper(),
            NintendoShopScraper(),
        ]

    async def get_prices(self, game_title: str) -> List[Dict]:
        prices = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for scraper in self.scrapers:
                scraper.session = session
                tasks.append(scraper.search_game(game_title))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict):
                    prices.append(result)

        return prices

    async def get_multiple_game_prices(
        self, game_title: str, limit: int = 10
    ) -> Dict[str, List[Dict]]:
        """Get prices for multiple games matching the search term across all platforms"""
        results = {"Steam": []}

        # Only Steam scraper currently supports multiple game search
        async with aiohttp.ClientSession() as session:
            steam_scraper = SteamScraper()
            steam_scraper.session = session

            # Get multiple games from Steam
            if hasattr(steam_scraper, "search_multiple_games"):
                steam_results = await steam_scraper.search_multiple_games(
                    game_title, limit
                )
                if steam_results:
                    results["Steam"] = steam_results

        return results


# Usage example:
# async def main():
#     aggregator = GamePriceAggregator()
#     prices = await aggregator.get_prices('Cyberpunk 2077')
#     print(prices)
#
# if __name__ == '__main__':
#     asyncio.run(main())
