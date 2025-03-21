# H&M Fashion Assistant API Documentation

This document provides information on how to use the H&M Fashion Assistant API for integration with mobile apps and other clients.

## Base URL

When running locally:

```
http://localhost:8000
```

## Authentication

Currently, the API does not implement authentication. For production use, you should implement an appropriate authentication mechanism.

## Endpoints

### 1. Chat with Fashion Assistant

**Endpoint:** `/api/chat`

**Method:** POST

**Description:** Send a query to the fashion assistant and get a response.

**Request Body:**

```json
{
  "query": "I need a casual outfit for summer",
  "session_id": "optional-session-id-for-continuing-conversation"
}
```

- `query` (required): The user's fashion query or message
- `session_id` (optional): A unique identifier for the conversation session. If not provided, a new session will be created.

**Response:**

```json
{
  "response": "For a casual summer outfit, I recommend...",
  "products": [
    {
      "name": "Loose Fit T-shirt",
      "price": "$9.99",
      "image_url": "https://image.hm.com/assets/hm/7b/17/7b17428dc1da8df6b8b054f8729b58bd8d06e60a.jpg",
      "product_link": "https://www2.hm.com/en_us/productpage.0608945124.html",
      "category": "Men",
      "colors": "Yellow, Black, White, Dark beige, Light beige, Pink, Light sage green, Dark gray, Navy blue"
    },
    {
      "name": "Loose-Fit Seersucker Resort Shirt",
      "price": "$29.99",
      "image_url": "https://image.hm.com/assets/hm/d2/d2/d2d2cb5c3cf01c2c650aefe1d45546d0b61dcad6.jpg",
      "product_link": "https://www2.hm.com/en_us/productpage.1265306004.html",
      "category": "Men",
      "colors": "Light blue/striped, Beige/checked, Dark gray"
    }
  ],
  "session_id": "session-id-for-continuing-conversation"
}
```

- `response`: The fashion assistant's text response
- `products`: An array of product details including:
  - `name`: The product name
  - `price`: The product price
  - `image_url`: URL to the product image
  - `product_link`: URL to the product page
  - `category`: Product category (e.g., Men, Women, Kids)
  - `colors`: Available colors for the product
- `session_id`: The session ID to use for continuing the conversation

### 2. Reset Conversation Session

**Endpoint:** `/api/reset`

**Method:** POST

**Description:** Reset a conversation session to start fresh.

**Request Body:**

```json
{
  "session_id": "session-id-to-reset"
}
```

- `session_id` (required): The session ID to reset

**Response:**

```json
{
  "success": true,
  "session_id": "session-id-that-was-reset"
}
```

### 3. Health Check

**Endpoint:** `/api/health`

**Method:** GET

**Description:** Check if the API is running.

**Response:**

```json
{
  "status": "ok"
}
```

## Example Usage

### Python Example

```python
import requests

API_URL = "http://localhost:8000"

# Start a conversation
response = requests.post(f"{API_URL}/api/chat", json={
    "query": "I need a casual outfit for summer"
})
data = response.json()
session_id = data["session_id"]
print(data["response"])

# Display product information
for product in data.get("products", []):
    print(f"{product['name']} - {product['price']}")
    print(f"Link: {product['product_link']}")

# Continue the conversation
response = requests.post(f"{API_URL}/api/chat", json={
    "query": "Do you have any in blue?",
    "session_id": session_id
})
data = response.json()
print(data["response"])
```

### Mobile App Integration

For mobile apps, you can:

1. Make HTTP requests to the API endpoints
2. Store the session_id in the app's local storage
3. Send the session_id with each request to maintain conversation context
4. Display the assistant's responses and product details in your UI:
   - Show product images using the image_url
   - Display product names and prices
   - Create clickable links to the product pages
   - Show available colors and categories

## Error Handling

The API returns standard HTTP status codes:

- 200: Success
- 400: Bad request (missing parameters)
- 500: Server error

Error responses include an error message:

```json
{
  "error": "Missing query parameter"
}
```

## Session Management

- Sessions are maintained on the server for continuing conversations
- Each session has a unique ID
- Sessions store conversation history
- The server automatically limits conversation history to prevent context overflow
- Old sessions are cleaned up periodically

## Deployment Considerations

For production deployment:

1. Add proper authentication
2. Use HTTPS
3. Set up rate limiting
4. Consider using a production-ready server like Gunicorn
5. Implement proper logging
6. Add monitoring
7. Consider containerization with Docker
