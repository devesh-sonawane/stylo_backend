import asyncio
import json
from enhanced_steam_scraper import EnhancedSteamScraper


async def test_single_game_search():
    """Test searching for a single game"""
    print("\n=== Testing Single Game Search ===")
    async with EnhancedSteamScraper() as scraper:
        # Test with a game name
        game_name = "Cyberpunk 2077"
        print(f"\nSearching for: {game_name}")
        result = await scraper.search_game(game_name)
        if result:
            print(f"Found: {result['title']}")
            print(f"Price: {result['price']} {result['currency']}")
            if result["is_sale"]:
                print(f"On sale! {result['discount_percent']}% off")
                print(f"Original price: {result['initial_price']} {result['currency']}")
            print(f"URL: {result['url']}")
        else:
            print(f"No results found for {game_name}")

        # Test with an app ID
        app_id = "730"  # CS:GO
        print(f"\nSearching for app ID: {app_id}")
        result = await scraper.search_game(app_id)
        if result:
            print(f"Found: {result['title']}")
            print(f"Price: {result['price']} {result['currency']}")
            if result["is_sale"]:
                print(f"On sale! {result['discount_percent']}% off")
                print(f"Original price: {result['initial_price']} {result['currency']}")
            print(f"URL: {result['url']}")
        else:
            print(f"No results found for app ID {app_id}")


async def test_multiple_games_search():
    """Test searching for multiple games"""
    print("\n=== Testing Multiple Games Search ===")
    async with EnhancedSteamScraper() as scraper:
        search_term = "fallout"
        limit = 5
        print(f"\nSearching for up to {limit} games matching: {search_term}")
        results = await scraper.search_multiple_games(search_term, limit)

        if results:
            print(f"Found {len(results)} games:")
            for i, game in enumerate(results, 1):
                print(f"\n{i}. {game['title']}")
                print(f"   Price: {game['price']} {game['currency']}")
                if game["is_sale"]:
                    print(f"   On sale! {game['discount_percent']}% off")
                    print(
                        f"   Original price: {game['initial_price']} {game['currency']}"
                    )
                print(f"   URL: {game['url']}")
        else:
            print(f"No results found for {search_term}")


async def test_price_aggregator():
    """Test the integration with the price aggregator"""
    print("\n=== Testing Price Aggregator Integration ===")
    from price_scrapers import GamePriceAggregator

    aggregator = GamePriceAggregator()
    game_title = "Elden Ring"

    print(f"\nGetting prices for: {game_title}")
    prices = await aggregator.get_prices(game_title)

    if prices:
        print(f"Found prices on {len(prices)} platforms:")
        for price in prices:
            print(f"\n{price['platform']}: {price['title']}")
            print(f"Price: {price['price']} {price['currency']}")
            if price.get("is_sale"):
                print(f"On sale! {price.get('discount_percent', 0)}% off")
            print(f"URL: {price['url']}")
    else:
        print(f"No prices found for {game_title}")

    # Test multiple game search if available
    if hasattr(aggregator, "get_multiple_game_prices"):
        search_term = "mario"
        print(f"\nSearching for multiple games matching: {search_term}")
        multi_results = await aggregator.get_multiple_game_prices(search_term, limit=3)

        if multi_results and any(multi_results.values()):
            for platform, games in multi_results.items():
                if games:
                    print(f"\nFound {len(games)} games on {platform}:")
                    for i, game in enumerate(games, 1):
                        print(
                            f"  {i}. {game['title']}: {game['price']} {game['currency']}"
                        )
        else:
            print(f"No multiple game results found for {search_term}")


async def main():
    """Run all tests"""
    await test_single_game_search()
    await test_multiple_games_search()
    await test_price_aggregator()


if __name__ == "__main__":
    asyncio.run(main())
