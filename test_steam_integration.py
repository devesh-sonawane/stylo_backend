import asyncio
from enhanced_steam_scraper import EnhancedSteamScraper


async def test_steam_scraper():
    """Test the EnhancedSteamScraper functionality"""
    print("\n=== Testing Steam Scraper Integration ===\n")

    # Test with a specific game query
    test_games = ["Cyberpunk 2077", "Elden Ring", "Baldur's Gate 3", "Starfield"]

    async with EnhancedSteamScraper() as scraper:
        for game in test_games:
            print(f"Searching for: {game}")
            result = await scraper.search_game(game)
            if result:
                print(f"Found game: {result['title']}")
                print(f"Price: {result['price']} {result['currency']}")
                print(f"Platform: {result['platform']}")
                print(f"Genres: {', '.join(result['genres'])}")
                print(
                    f"Available on: {', '.join([platform for platform, available in result['platforms'].items() if available])}"
                )
                print(f"On sale: {'Yes' if result['is_sale'] else 'No'}")
                if result["is_sale"]:
                    print(f"Discount: {result['discount_percent']}%")
                    print(
                        f"Original price: {result['initial_price']} {result['currency']}"
                    )
                print(f"URL: {result['url']}")
            else:
                print(f"No game information found for: {game}")
            print("\n---\n")


if __name__ == "__main__":
    asyncio.run(test_steam_scraper())
