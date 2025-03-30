import asyncio
from game_agent import GameAgent


async def test_game_info():
    """Test the game information retrieval functionality"""
    print("\n=== Testing Game Information Retrieval ===\n")
    agent = GameAgent()

    # Test with a specific game query
    test_queries = [
        "What is the price of Cyberpunk 2077?",
        "Tell me about Elden Ring",
        "How much does Baldur's Gate 3 cost?",
        "Is Starfield on sale?",
    ]

    for query in test_queries:
        print(f"Query: {query}")
        result = await agent._get_game_info(query)
        if result:
            print(f"Found game: {result['title']}")
            print(f"Price: {result['price']}")
            print(f"Platform: {result['platform']}")
            print(f"Genres: {result['genres']}")
            print(f"Available on: {result['platforms']}")
            print(f"On sale: {result['on_sale']}")
            if result["on_sale"] == "Yes":
                print(f"Discount: {result['discount']}")
                print(f"Original price: {result['original_price']}")
            print(f"URL: {result['url']}")
        else:
            print(f"No game information found for query: {query}")
        print("\n---\n")

    # Test the chat functionality with game info
    print("\n=== Testing Chat with Game Information ===\n")
    chat_response = await agent.chat("What's the price of Hades?")
    print(f"Chat response: {chat_response['response']}")


if __name__ == "__main__":
    asyncio.run(test_game_info())
