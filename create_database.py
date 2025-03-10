from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import pandas as pd
import openai 
from dotenv import load_dotenv
import os
import shutil

# Load environment variables. Assumes that project contains .env file with API keys
load_dotenv()
#---- Set OpenAI API key 
# Change environment variable name from "OPENAI_API_KEY" to the name given in 
# your .env file.
openai.api_key = os.environ['OPENAI_API_KEY']

CHROMA_PATH = "chroma_fashion"
DATA_PATH = "data/h&m/hm_products.csv"


def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = process_documents(documents)
    save_to_chroma(chunks)


def load_documents():
    """Load the H&M product data from CSV using pandas directly for better control"""
    # Read the CSV file using pandas
    df = pd.read_csv(DATA_PATH)
    
    # Create documents from each row
    documents = []
    for _, row in df.iterrows():
        # Extract data from row
        category = row.get('Category', '')
        name = row.get('Name', '')
        price = row.get('Price', '')
        colors = row.get('Colors', '')
        image = row.get('Image', '')
        product_link = row.get('Product Link', '')
        
        # Create content string
        content = f"""
Product: {name}
Category: {category}
Price: {price}
Available Colors: {colors}
Image URL: {image}
Product Link: {product_link}

This is a {category} product from H&M called "{name}" available for {price}. 
It comes in the following colors: {colors}.
"""
        
        # Create document with metadata
        doc = Document(
            page_content=content.strip(),
            metadata={
                "Category": category,
                "Name": name,
                "Price": price,
                "Colors": colors,
                "Image": image,
                "Product Link": product_link,
                "source": product_link  # For compatibility with existing code
            }
        )
        documents.append(doc)
    
    print(f"Loaded {len(documents)} products from CSV")
    return documents


def process_documents(documents: list[Document]):
    """Process documents into chunks for embedding"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
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
    
    db = Chroma.from_documents(
        chunks, embeddings, persist_directory=CHROMA_PATH
    )
    # db.persist() - No longer needed as Chroma 0.4.x automatically persists documents
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    main()
