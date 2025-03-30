import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_chat(query, session_id=None):
    """Test the chat API endpoint"""
    url = f"{API_URL}/api/chat"
    
    payload = {
        "query": query
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    print(f"\nSending query: '{query}'")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n" + "="*70)
        print("RESPONSE:")
        print("="*70)
        print(data["response"])
        
        if data.get("products"):
            print("\nPRODUCT DETAILS:")
            for i, product in enumerate(data["products"], 1):
                print(f"{i}. {product.get('name', 'No name')} - {product.get('price', 'No price')}")
                print(f"   Category: {product.get('category', 'N/A')}")
                print(f"   Colors: {product.get('colors', 'N/A')}")
                print(f"   Image: {product.get('image_url', 'No image')}")
                print(f"   Link: {product.get('product_link', 'No link')}")
                print()
        
        print("-"*70)
        return data.get("session_id")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def reset_session(session_id):
    """Test the reset API endpoint"""
    url = f"{API_URL}/api/reset"
    
    payload = {
        "session_id": session_id
    }
    
    print(f"\nResetting session: {session_id}")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Session reset successfully: {data['session_id']}")
        return data.get("session_id")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def test_conversation():
    """Test a multi-turn conversation"""
    # First query
    session_id = test_chat("Suggest me T-shirt under $40 for winter")
    
    if not session_id:
        return
    
    # Follow-up query
    test_chat("I can increase my budget to $50", session_id)
    
    # Another follow-up
    test_chat("I also want a pair of jeans", session_id)
    
    # Thank you message
    test_chat("Thank you for your help!", session_id)
    
    # Reset the session
    reset_session(session_id)
    
    # New query after reset
    test_chat("I need a business outfit", session_id)

def test_health():
    """Test the health check endpoint"""
    url = f"{API_URL}/api/health"
    
    print("\nChecking API health...")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"API Status: {data['status']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Check if the API is running
    try:
        test_health()
        
        if len(sys.argv) > 1:
            # Single query mode
            query = " ".join(sys.argv[1:])
            test_chat(query)
        else:
            # Test conversation mode
            test_conversation()
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the server is running with: python api_server.py") 