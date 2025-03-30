import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from tqdm import tqdm
import shutil

# Load environment variables
load_dotenv()

# Constants
GAME_EMBEDDINGS_PATH = "./game_embeddings"
GAMES_CSV_PATH = "/Users/deveshsonawane/Devesh_Workspace/Spring_2025/GenAI/GamingAI/game-backend/data/games.csv"  # Path to games CSV file


def main():
    """Generate game embeddings and save to vector store"""
    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        return

    # Initialize embedding model
    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", google_api_key=api_key
    )

    # Load games data
    try:
        games_df = pd.read_csv(GAMES_CSV_PATH)
        print(f"Loaded {len(games_df)} games from CSV")
    except FileNotFoundError:
        print(f"Error: Games CSV file not found at {GAMES_CSV_PATH}")
        return
    except Exception as e:
        print(f"Error loading games data: {e}")
        return

    # Create documents from games data
    documents = []
    for _, game in tqdm(
        games_df.iterrows(), total=len(games_df), desc="Processing games"
    ):
        # Extract game data
        game_id = str(game.get("id", ""))
        title = game.get("title", "")
        description = game.get("description", "")
        genres = game.get("genres", "")
        price = game.get("price", "Price not available")
        release_date = game.get("release_date", "")
        developers = game.get("developers", "")
        publishers = game.get("publishers", "")
        platforms = game.get("platforms", "")
        metacritic_score = game.get("metacritic_score", 0)
        image_url = game.get("image_url", "")
        website = game.get("website", "")

        # Create content string
        content = {
            "id": game_id,
            "title": title,
            "description": description,
            "genres": genres,
            "price": price,
            "release_date": release_date,
            "developers": developers,
            "publishers": publishers,
            "platforms": platforms,
            "metacritic_score": metacritic_score,
            "image_url": image_url,
            "website": website,
        }

        # Create document with metadata
        doc = Document(
            page_content=json.dumps(content),
            metadata={"id": game_id, "title": title, "genres": genres, "price": price},
        )
        documents.append(doc)

    # Clear existing vector store if it exists
    if os.path.exists(GAME_EMBEDDINGS_PATH):
        print(f"Removing existing vector store at {GAME_EMBEDDINGS_PATH}")
        shutil.rmtree(GAME_EMBEDDINGS_PATH)

    # Create and persist vector store
    print(f"Creating vector store with {len(documents)} documents")
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=GAME_EMBEDDINGS_PATH,
    )
    vectorstore.persist()
    print(f"Vector store created and saved to {GAME_EMBEDDINGS_PATH}")


if __name__ == "__main__":
    main()
