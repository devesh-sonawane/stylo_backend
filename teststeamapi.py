import os
import requests
import time
from steam.webapi import WebAPI

KEY = "8F3C865FCFC0FC9D344A7B55569FBC6B"

# Initialize the Steam Web API with rate limiting
api = WebAPI(key=KEY)

# Common game variations and their app IDs
POPULAR_GAMES = {
    "counter strike global offensive": 730,
    "csgo": 730,
    "cs go": 730,
    "cs:go": 730,
}


def normalize_game_name(name):
    # Remove special characters and extra spaces
    name = name.lower()
    name = name.replace(":", "")
    name = name.replace("-", " ")
    return " ".join(name.split())


def is_valid_app_id(app_id_str):
    try:
        app_id = int(app_id_str)
        return app_id > 0
    except ValueError:
        return False


def get_game_details(appid):
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
                if not data:
                    print(f"No data returned for appid {appid}")
                    return None

                if str(appid) not in data:
                    print(f"Invalid response format for appid {appid}")
                    return None

                app_data = data[str(appid)]
                if not app_data.get("success"):
                    print(f"Failed to get data for appid {appid}")
                    return None

                game_data = app_data["data"]
                if not game_data:
                    print(f"Empty game data for appid {appid}")
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
                    }
                elif game_data.get("is_free", False):
                    return {
                        "name": game_data.get("name", ""),
                        "price": "Free to Play",
                        "discount": 0,
                        "initial_price": None,
                    }
                else:
                    print(
                        f"No price information available for {game_data.get('name', f'appid {appid}')}"
                    )
                    return None
            except ValueError as e:
                print(f"Failed to parse JSON response for appid {appid}: {e}")
                return None
        else:
            print(f"Failed to fetch game details. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching game details: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while fetching game details: {e}")
        return None


# Get user input for game search
game_name = input("Enter the game name or app ID to search: ")

try:
    # Check if input is an app ID
    if is_valid_app_id(game_name):
        details = get_game_details(int(game_name))
        if details:
            discount_info = (
                f" (Was {details['initial_price']}, -{details['discount']}% OFF)"
                if details.get("discount", 0) > 0
                else ""
            )
            print(
                f"\nFound game:\n- {details['name']}: {details['price']}{discount_info}"
            )
        else:
            print("No game found with that app ID.")
        exit()

    # If not an app ID, check for popular games first
    normalized_search = normalize_game_name(game_name)
    if normalized_search in POPULAR_GAMES:
        details = get_game_details(POPULAR_GAMES[normalized_search])
        if details:
            discount_info = (
                f" (Was {details['initial_price']}, -{details['discount']}% OFF)"
                if details.get("discount", 0) > 0
                else ""
            )
            print(
                f"\nFound game:\n- {details['name']}: {details['price']}{discount_info}"
            )
            exit()

    # Get app details with retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            apps = api.ISteamApps.GetAppList()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed. Retrying...")
                time.sleep(2)
            else:
                raise e

    # Improved search algorithm with better filtering
    excluded_terms = [
        "skin",
        "soundtrack",
        "dlc",
        "trailer",
        "demo",
        "server",
        "dedicated",
        "test",
    ]

    # First try exact match with normalized names
    results = [
        app
        for app in apps["applist"]["apps"]
        if normalized_search == normalize_game_name(app["name"])
        and not any(term in app["name"].lower() for term in excluded_terms)
    ]

    # If no exact matches, try contains match but exclude non-game items
    if not results:
        results = [
            app
            for app in apps["applist"]["apps"]
            if normalized_search in normalize_game_name(app["name"])
            and not any(term in app["name"].lower() for term in excluded_terms)
        ]

    if not results:
        print("No games found matching your search.")
        exit()

    print("\nFound games:")
    found_games = 0
    for app in results:
        if found_games >= 10:
            break

        details = get_game_details(app["appid"])
        if details:
            found_games += 1
            discount_info = (
                f" (Was {details['initial_price']}, -{details['discount']}% OFF)"
                if details.get("discount", 0) > 0
                else ""
            )
            print(f"- {details['name']}: {details['price']}{discount_info}")

    if len(results) > 10:
        print(
            "\nShowing first 10 results only. Please refine your search for more specific results."
        )
    elif found_games == 0:
        print("\nNo price information available for any of the found games.")

except Exception as e:
    print(f"Error: {str(e)}")
    print("Please check your internet connection and Steam API key.")
