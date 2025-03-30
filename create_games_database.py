from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import openai
from dotenv import load_dotenv
import os
import shutil
from tqdm import tqdm

# Load environment variables. Assumes that project contains .env file with API keys
load_dotenv()
# ---- Set OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

CHROMA_PATH = "chroma_games"
DATA_PATH = "../dataset/games.json"


def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = process_documents(documents)
    save_to_chroma(chunks)


def load_documents():
    """Load the Steam games data from JSON"""
    # Read the JSON file
    with open(DATA_PATH, "r") as f:
        games_data = json.load(f)

    # Create documents from each game
    documents = []
    for game_id, game in tqdm(games_data.items(), desc="Loading games", unit="game"):
        # Extract data from game
        name = game.get("name", "")
        description = game.get(
            "detailed_description", game.get("short_description", "")
        )
        price = game.get("price_overview", {}).get(
            "final_formatted", "Price not available"
        )
        categories = ", ".join(
            [cat for cat in game.get("categories", []) if isinstance(cat, str)]
            or [
                cat.get("description", "")
                for cat in game.get("categories", [])
                if isinstance(cat, dict)
            ]
        )
        genres = ", ".join(
            [genre for genre in game.get("genres", []) if isinstance(genre, str)]
            or [
                genre.get("description", "")
                for genre in game.get("genres", [])
                if isinstance(genre, dict)
            ]
        )
        header_image = game.get("header_image", "")
        website = game.get("website", "")
        developers = ", ".join(game.get("developers", []))
        publishers = ", ".join(game.get("publishers", []))
        # Handle release_date which can be either a string or a dictionary with a 'date' key
        release_date_data = game.get("release_date", "")
        if isinstance(release_date_data, dict):
            release_date = release_date_data.get("date", "")
        else:
            release_date = release_date_data
        metacritic_score = game.get("metacritic_score", 0)

        # Create content string
        content = f"""
Game: {name}
Genres: {genres}
Categories: {categories}
Price: {price}
Developers: {developers}
Publishers: {publishers}
Release Date: {release_date}
Metacritic Score: {metacritic_score}
Image URL: {header_image}
Website: {website}

Description: {description}

This is a {genres} game called "{name}" available for {price}. 
It was developed by {developers} and published by {publishers}.
It was released on {release_date} and has a Metacritic score of {metacritic_score}.
"""

        # Create document with metadata
        doc = Document(
            page_content=content.strip(),
            metadata={
                "Game ID": game_id,
                "Name": name,
                "Genres": genres,
                "Categories": categories,
                "Price": price,
                "Developers": developers,
                "Publishers": publishers,
                "Release Date": release_date,
                "Metacritic Score": str(metacritic_score),
                "Image": header_image,
                "Website": website,
                "source": website
                or header_image,  # For compatibility with existing code
            },
        )
        documents.append(doc)

    print(f"Loaded {len(documents)} games from JSON")
    return documents


def process_documents(documents: list[Document]):
    """Process documents into chunks for embedding"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )
    print("Splitting documents into chunks...")
    chunks = text_splitter.split_documents(
        tqdm(documents, desc="Processing documents", unit="doc")
    )
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    if chunks:
        # Print a sample chunk to verify the content
        document = chunks[0]
        print("Sample chunk content:")
        print(document.page_content)
        print("Sample chunk metadata:")
        print(document.metadata)

    return chunks


def save_to_chroma(chunks: list[Document]):
    """Save chunks to Chroma vector database"""
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents.
    # Initialize OpenAI embeddings with the API key
    embeddings = OpenAIEmbeddings()

    print("Saving chunks to Chroma database...")
    # Using tqdm to show progress while saving to Chroma
    # Note: We can't directly wrap Chroma.from_documents with tqdm, so we show a message
    # to indicate the process is running
    db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")
    print("Database creation complete!")


if __name__ == "__main__":
    main()
