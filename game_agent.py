import os
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from enhanced_steam_scraper import EnhancedSteamScraper

# Load environment variables
load_dotenv()


class GameAgent:
    """AI agent for game recommendations and chat interactions"""

    def __init__(self, db_directory: str = "./game_embeddings"):
        """Initialize the game agent with embeddings and LLM"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        # Initialize the embedding model
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", google_api_key=self.api_key
        )

        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
        )

        # Set up the vector store if it exists
        self.db_directory = db_directory
        try:
            self.vectorstore = Chroma(
                persist_directory=db_directory, embedding_function=self.embedding_model
            )
            print(f"Loaded existing vector store from {db_directory}")
        except Exception as e:
            print(f"Vector store not found or error loading: {e}")
            self.vectorstore = None

    def _create_game_chat_chain(self):
        """Create a chain for game-related chat responses"""
        # Define the system prompt
        system_template = """
        You are a helpful gaming assistant that provides information about video games.
        Use the following context about games to answer the user's question.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        """

        # Define the human prompt
        human_template = "{question}"

        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_template), ("human", human_template)]
        )

        # Create the chain
        chain = (
            {"context": self._retrieve_context, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return chain

    def _retrieve_context(self, query: str) -> str:
        """Retrieve relevant game context from the vector store"""
        if not self.vectorstore:
            return "No game information available."

        # Get relevant documents from the vector store
        docs = self.vectorstore.similarity_search(query, k=5)

        # Format the context
        context = "\n\n".join([doc.page_content for doc in docs])
        return context

    async def chat(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Process a chat message and return a response"""
        # Create the chain if not already created
        chain = self._create_game_chat_chain()

        # Check if the message is asking about a specific game
        if any(
            keyword in message.lower()
            for keyword in [
                "price",
                "cost",
                "how much",
                "discount",
                "sale",
                "information about",
                "tell me about",
                "details on",
                "info on",
            ]
        ):
            # Try to extract game information
            game_info = await self._get_game_info(message)
            if game_info:
                # Enhance the response with game information
                enhanced_message = f"{message}\n\nHere is the information about the game:\n{json.dumps(game_info, indent=2)}"
                response = chain.invoke(enhanced_message)
                return {
                    "response": response,
                    "session_id": session_id or str(uuid.uuid4()),
                }

        # Process the message normally
        response = chain.invoke(message)
        return {"response": response, "session_id": session_id or str(uuid.uuid4())}

    async def search_games(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for games based on a query"""
        if not self.vectorstore:
            return []

        # Search for similar games
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=limit)

        # Format the results
        results = []
        for doc, score in docs_and_scores:
            # Extract game data from the document
            try:
                game_data = json.loads(doc.page_content)
                game_data["relevance_score"] = float(score)
                results.append(game_data)
            except json.JSONDecodeError:
                # If the document isn't valid JSON, use the raw content
                results.append(
                    {
                        "title": doc.metadata.get("title", "Unknown Game"),
                        "description": doc.page_content,
                        "relevance_score": float(score),
                    }
                )

        return results

    async def recommend_games(
        self, preferences: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Recommend games based on user preferences"""
        # Use the search function with the preferences as the query
        return await self.search_games(preferences, limit)

    async def _get_game_info(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract game information using the EnhancedSteamScraper"""
        # Try to extract the game title from the message
        # This is a simple implementation - could be improved with NLP
        lower_message = message.lower()
        game_title = None

        # Look for common patterns that might indicate a game title
        patterns = [
            "about",
            "for",
            "on",
            "of",
            "called",
            "named",
            "titled",
            "game",
            "price of",
            "cost of",
            "information on",
        ]

        for pattern in patterns:
            if pattern in lower_message:
                parts = lower_message.split(pattern, 1)
                if len(parts) > 1 and parts[1].strip():
                    # Take the part after the pattern as potential game title
                    potential_title = parts[1].strip()
                    # Remove common question endings
                    for ending in [
                        "?",
                        ".",
                        "!",
                        "cost",
                        "price",
                        "on sale",
                        "discount",
                    ]:
                        potential_title = potential_title.split(ending)[0].strip()
                    if potential_title:
                        game_title = potential_title
                        break

        # If no pattern matched, try to use the whole message
        if not game_title and any(
            word in lower_message for word in ["price", "cost", "discount", "sale"]
        ):
            # Remove question words and common phrases
            for word in [
                "what",
                "is",
                "the",
                "price",
                "of",
                "cost",
                "for",
                "how",
                "much",
                "does",
                "?",
            ]:
                lower_message = lower_message.replace(word, " ")
            game_title = lower_message.strip()

        if not game_title:
            return None

        try:
            # Use the EnhancedSteamScraper to get game information
            async with EnhancedSteamScraper() as scraper:
                result = await scraper.search_game(game_title)
                if result:
                    # Format the result for better readability
                    formatted_result = {
                        "title": result["title"],
                        "price": f"{result['price']} {result['currency']}",
                        "platform": result["platform"],
                        "url": result["url"],
                        "genres": (
                            ", ".join(result["genres"])
                            if result["genres"]
                            else "Not specified"
                        ),
                        "platforms": self._format_platforms(result["platforms"]),
                    }

                    # Add sale information if applicable
                    if result["is_sale"]:
                        formatted_result["on_sale"] = "Yes"
                        formatted_result["discount"] = f"{result['discount_percent']}%"
                        formatted_result["original_price"] = (
                            f"{result['initial_price']} {result['currency']}"
                        )
                    else:
                        formatted_result["on_sale"] = "No"

                    return formatted_result
        except Exception as e:
            print(f"Error getting game info: {e}")

        return None

    def _format_platforms(self, platforms_dict: Dict[str, bool]) -> str:
        """Format the platforms dictionary into a readable string"""
        if not platforms_dict:
            return "Not specified"

        available_platforms = [
            platform for platform, available in platforms_dict.items() if available
        ]
        if not available_platforms:
            return "Not specified"

        return ", ".join(available_platforms)
