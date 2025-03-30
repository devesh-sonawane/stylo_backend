from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
import os
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Configuration
CHROMA_PATH = "chroma_games"

# System template for the gaming assistant
SYSTEM_TEMPLATE = """
You are a helpful and knowledgeable gaming assistant. Your job is to recommend games based on the user's query and the game information provided.

When recommending games, be sure to:
1. Address the user's query directly
2. Recommend specific games from the retrieved game information that match their needs
3. Mention game details like price, genres, developers, and release date
4. Offer gaming advice when appropriate
5. Be friendly and conversational
6. Refer to previous parts of the conversation when relevant

If the user says something like "thank you" or asks a question unrelated to games, respond appropriately without trying to recommend games.

Remember previous interactions with the user to provide more personalized recommendations.
"""

# Store conversation sessions
sessions = {}


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    API endpoint for chatting with the gaming assistant

    Expected JSON payload:
    {
        "query": "I need a casual outfit for summer",
        "session_id": "optional-session-id-for-continuing-conversation"
    }

    Returns:
    {
        "response": "Assistant's response text",
        "products": [
            {
                "name": "Product Name",
                "price": "$XX.XX",
                "image_url": "https://example.com/image.jpg",
                "product_link": "https://example.com/product",
                "category": "Category",
                "colors": "Available colors"
            },
            ...
        ],
        "session_id": "session-id-for-continuing-conversation"
    }
    """
    try:
        data = request.json

        if not data or "query" not in data:
            return jsonify({"error": "Missing query parameter"}), 400

        query = data["query"]
        session_id = data.get("session_id", str(uuid.uuid4()))

        # Get or create session
        if session_id not in sessions:
            sessions[session_id] = {
                "chat_history": [SystemMessage(content=SYSTEM_TEMPLATE)],
                "original_query": query,  # Store the original query
            }

        # Get chat history and original query
        chat_history = sessions[session_id]["chat_history"]
        original_query = sessions[session_id].get("original_query", "")

        # Add user query to chat history
        chat_history.append(HumanMessage(content=query))

        # Initialize models
        embedding_function = OpenAIEmbeddings()
        db = Chroma(
            persist_directory=CHROMA_PATH, embedding_function=embedding_function
        )
        llm = ChatOpenAI(temperature=0.7)

        products = []

        # Determine if this is a casual response or needs game search
        if any(
            word in query.lower()
            for word in ["thank", "thanks", "appreciate", "helpful"]
        ):
            # For thank you messages, respond without searching games
            prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content="You are a friendly gaming assistant. Respond to the user's gratitude politely."
                    ),
                    *chat_history,
                ]
            )
            formatted_prompt = prompt.format_messages()
            response = llm.invoke(formatted_prompt)

        else:
            # For gaming queries, search for relevant games
            # If this is a follow-up query with additional information, combine with original query for better context
            search_query = query
            if len(chat_history) > 2 and not query.lower().startswith(
                ("i need", "suggest", "recommend", "show me", "find me")
            ):
                # This appears to be a refinement query, not a new request
                search_query = f"{original_query} {query}"
                print(f"Enhanced search query: {search_query}")

            results = db.similarity_search_with_relevance_scores(search_query, k=5)

            if len(results) == 0 or results[0][1] < 0.6:
                response_text = "I'm sorry, I couldn't find any games matching your query. Could you try rephrasing or asking about something else?"
                response = AIMessage(content=response_text)
            else:
                # Create context from retrieved documents
                context_text = "\n\n---\n\n".join(
                    [doc.page_content for doc, _score in results]
                )

                # Extract game details for the response
                for doc, _ in results:
                    metadata = doc.metadata
                    game_link = metadata.get("Website", "")
                    if not game_link:
                        game_link = f"https://store.steampowered.com/app/{metadata.get('Game ID', '')}"

                    game = {
                        "name": metadata.get("Name", ""),
                        "price": metadata.get("Price", ""),
                        "image_url": metadata.get("Image", ""),
                        "product_link": game_link,
                        "genres": metadata.get("Genres", ""),
                        "developers": metadata.get("Developers", ""),
                        "publishers": metadata.get("Publishers", ""),
                        "release_date": metadata.get("Release Date", ""),
                        "metacritic_score": metadata.get("Metacritic Score", ""),
                    }
                    # Only add games with valid links and names
                    if game["product_link"] and game["name"]:
                        # Check if this game is already in the list (avoid duplicates)
                        if not any(
                            p["product_link"] == game["product_link"] for p in products
                        ):
                            products.append(game)

                # Create prompt with chat history, original query context, and retrieved context
                prompt = ChatPromptTemplate.from_messages(
                    [
                        SystemMessage(content=SYSTEM_TEMPLATE),
                        *chat_history[
                            1:
                        ],  # Skip the system message as we're adding it explicitly above
                        HumanMessage(
                            content=f"Here is game information that might be relevant to the user's request. Remember that the original request was about: '{original_query}'\n\n{context_text}"
                        ),
                    ]
                )

                formatted_prompt = prompt.format_messages()
                response = llm.invoke(formatted_prompt)

        # Add assistant response to chat history
        chat_history.append(response)

        # Limit chat history to last 10 messages to prevent context overflow
        if len(chat_history) > 11:  # 1 system message + 10 conversation messages
            chat_history = [chat_history[0]] + chat_history[-10:]
            sessions[session_id]["chat_history"] = chat_history

        # Clean up old sessions (optional, implement based on your needs)
        clean_old_sessions()

        return jsonify(
            {
                "response": response.content,
                "products": products[:5],  # Limit to 5 games
                "session_id": session_id,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_session():
    """
    Reset a conversation session

    Expected JSON payload:
    {
        "session_id": "session-id-to-reset"
    }

    Returns:
    {
        "success": true,
        "session_id": "session-id-that-was-reset"
    }
    """
    try:
        data = request.json

        if not data or "session_id" not in data:
            return jsonify({"error": "Missing session_id parameter"}), 400

        session_id = data["session_id"]

        if session_id in sessions:
            # Reset the session
            sessions[session_id] = {
                "chat_history": [SystemMessage(content=SYSTEM_TEMPLATE)]
            }
        else:
            # Create a new session
            sessions[session_id] = {
                "chat_history": [SystemMessage(content=SYSTEM_TEMPLATE)]
            }

        return jsonify({"success": True, "session_id": session_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def clean_old_sessions():
    """
    Clean up old sessions to prevent memory leaks
    This is a simple implementation - you might want to add timestamp-based cleanup
    """
    # For now, just ensure we don't have more than 1000 sessions
    if len(sessions) > 1000:
        # Remove oldest sessions (this is a simple approach)
        sessions_to_remove = list(sessions.keys())[:-900]  # Keep the 900 most recent
        for session_id in sessions_to_remove:
            del sessions[session_id]


@app.route("/api/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=8000, debug=True)
