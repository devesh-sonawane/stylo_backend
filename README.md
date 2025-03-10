# H&M Fashion Assistant

A conversational AI assistant that helps users find and style H&M products based on their preferences.

## Features

- **Product Recommendations**: Get personalized H&M product recommendations based on your fashion needs
- **Styling Advice**: Receive styling tips and outfit suggestions
- **Conversation Memory**: The assistant remembers previous interactions for more contextual responses
- **Multiple Interfaces**: Use the CLI, interactive mode, or API for integration with other applications

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd langchain-rag-tutorial
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

4. Create the vector database:

```bash
python create_database.py
```

## Usage

### Command Line Interface

Query the fashion assistant directly from the command line:

```bash
python query_data.py "I need a casual outfit for summer"
```

### Interactive Mode

Start an interactive conversation with the fashion assistant:

```bash
python query_data.py
```

### API Server

Start the API server for integration with other applications:

```bash
python api_server.py
```

The API server will run on http://localhost:8000. See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for details on the available endpoints and how to use them.

### Testing the API

Use the provided test script to test the API:

```bash
# Test with a single query
python test_api.py "I need a casual outfit for summer"

# Test a multi-turn conversation
python test_api.py
```

## Project Structure

- `create_database.py`: Processes the H&M product data and creates the vector database
- `query_data.py`: CLI and interactive interface for the fashion assistant
- `api_server.py`: API server for integration with other applications
- `test_api.py`: Script to test the API endpoints
- `API_DOCUMENTATION.md`: Detailed documentation of the API endpoints
- `data/h&m/`: Directory containing the H&M product data
- `chroma_fashion/`: Directory containing the vector database

## Mobile App Integration

To integrate with a mobile app:

1. Make HTTP requests to the API endpoints
2. Store the session_id in the app's local storage
3. Send the session_id with each request to maintain conversation context
4. Display the assistant's responses and product links in your UI

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for more details.

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses [LangChain](https://github.com/langchain-ai/langchain) for the RAG pipeline
- Product data from H&M
