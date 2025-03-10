import argparse
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import sys

CHROMA_PATH = "chroma_fashion"

SYSTEM_TEMPLATE = """
You are a helpful and knowledgeable fashion assistant for H&M. Your job is to recommend products based on the user's query and the product information provided.

When recommending products, be sure to:
1. Address the user's query directly
2. Recommend specific products from the retrieved product information that match their needs
3. Mention product details like price, colors, and category
4. Offer styling advice when appropriate
5. Be friendly and conversational
6. Refer to previous parts of the conversation when relevant

If the user says something like "thank you" or asks a question unrelated to fashion, respond appropriately without trying to recommend products.

Remember previous interactions with the user to provide more personalized recommendations.
"""

WELCOME_MESSAGE = """
🛍️ Welcome to the H&M Fashion Assistant! 🛍️

I can help you find the perfect outfit or item based on your preferences.
Just tell me what you're looking for, and I'll recommend H&M products that match your needs.

Examples of questions you can ask:
- "I need a casual outfit for summer"
- "What are some formal business attire options?"
- "Show me some comfortable loungewear"
- "I'm looking for accessories to match a black dress"

You can also follow up on previous questions to refine your search.
For example, after asking about summer outfits, you could say:
- "Do you have any in blue?"
- "What about something more formal?"
- "Can you suggest shoes to go with that?"

Type your fashion query below or type 'exit' to quit.
"""


def main():
    # Check if running in interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        # Create CLI for single query
        parser = argparse.ArgumentParser()
        parser.add_argument("query_text", type=str, help="The fashion query text.")
        args = parser.parse_args()
        query_text = args.query_text
        
        process_query(query_text)


def interactive_mode():
    """Run the fashion assistant in interactive mode with conversation memory"""
    print(WELCOME_MESSAGE)
    
    # Initialize the retriever
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Initialize the chat model
    llm = ChatOpenAI(temperature=0.7)
    
    # Initialize chat history
    chat_history = [
        SystemMessage(content=SYSTEM_TEMPLATE)
    ]
    
    while True:
        query = input("\n👗 Fashion Query: ")
        if query.lower() in ['exit', 'quit', 'q']:
            print("\nThank you for using the H&M Fashion Assistant! Have a stylish day! 👋")
            break
        
        print("\n⏳ Finding the perfect fashion recommendations for you...")
        
        # Add user query to chat history
        chat_history.append(HumanMessage(content=query))
        
        # Determine if this is a casual response or needs product search
        if any(word in query.lower() for word in ['thank', 'thanks', 'appreciate', 'helpful']):
            # For thank you messages, respond without searching products
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a friendly fashion assistant. Respond to the user's gratitude politely."),
                *chat_history
            ])
            formatted_prompt = prompt.format_messages()
            response = llm.invoke(formatted_prompt)
            
            # Set product_links to empty for thank you messages
            product_links = []
            
        else:
            # For fashion queries, search for relevant products
            results = db.similarity_search_with_relevance_scores(query, k=5)
            
            if len(results) == 0 or results[0][1] < 0.6:
                response_text = "I'm sorry, I couldn't find any products matching your query. Could you try rephrasing or asking about something else?"
                response = AIMessage(content=response_text)
            else:
                # Create context from retrieved documents
                context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
                
                # Create prompt with chat history and retrieved context
                prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=SYSTEM_TEMPLATE),
                    *chat_history[1:],  # Skip the system message as we're adding it explicitly above
                    HumanMessage(content=f"Here is product information that might be relevant to the user's latest query:\n\n{context_text}")
                ])
                
                formatted_prompt = prompt.format_messages()
                response = llm.invoke(formatted_prompt)
                
                # Extract product links for reference
                product_links = []
                for doc, _ in results:
                    link = doc.metadata.get("Product Link", "No link available")
                    if link != "No link available" and link not in product_links:
                        product_links.append(link)
        
        # Add assistant response to chat history
        chat_history.append(response)
        
        # Display the response
        print("\n" + "="*70)
        print("👚 FASHION ASSISTANT RESPONSE 👔")
        print("="*70)
        print(response.content)
        print("-"*70)
        
        # Display product links if available
        if 'product_links' in locals() and product_links:
            print("\n🔗 PRODUCT LINKS:")
            for i, link in enumerate(product_links[:5], 1):  # Limit to 5 links
                print(f"{i}. {link}")
            print("-"*70)


def process_query(query_text):
    """Process a single query without conversation memory"""
    # Prepare the DB.
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=5)
    if len(results) == 0 or results[0][1] < 0.6:  # Lower threshold for fashion queries
        print(f"\n❌ Unable to find matching products. Please try a different query.")
        return

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    # Create a prompt with system message
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_TEMPLATE),
        HumanMessage(content=f"Here is product information that might be relevant:\n\n{context_text}\n\nUser Query: {query_text}")
    ])
    
    print("\n⏳ Finding the perfect fashion recommendations for you...")
    
    model = ChatOpenAI(temperature=0.7)  # Slightly higher temperature for more creative responses
    formatted_prompt = prompt_template.format_messages()
    response = model.invoke(formatted_prompt)
    response_text = response.content

    # Extract product links for reference
    product_links = [doc.metadata.get("Product Link", "No link available") for doc, _score in results]
    
    print("\n" + "="*70)
    print("👚 FASHION ASSISTANT RESPONSE 👔")
    print("="*70)
    print(response_text)
    print("\n" + "-"*70)
    print("🔗 PRODUCT LINKS:")
    for i, link in enumerate(product_links, 1):
        print(f"{i}. {link}")
    print("-"*70)


if __name__ == "__main__":
    main()
