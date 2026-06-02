import fitz
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")
    
    document = fitz.open(pdf_path)
    full_text = " "

    for page_number in range(len(document)):
        page = document[page_number]
        full_text += page.getr_text()

    return full_text

import random
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text_into_chunks(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = splitter.split_text(text)
    return chunks

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import ollama

def upload_chunks_to_qdrant(pdf_path: str, collection_name: str = "monit_rag_collection"):
    print("[+] Extracting and splitting text from document...")
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text_into_chunks(text)
    
    client = QdrantClient(host="localhost", port=6333)
    
    if not client.collection_exists(collection_name):
        print(f"[+] Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
    
    print(f"[+] Generating embeddings for {len(chunks)} chunks with Ollama...")
    points = []
    for idx, chunk in enumerate(chunks):
        response = ollama.embeddings(model="nomic-embed-text", prompt=chunk)
        
        points.append(
            PointStruct(
                id=idx,
                vector=response["embedding"],
                payload={
                    "source": os.path.basename(pdf_path),
                    "content": chunk
                }
            )
        )
    
    print(f"[+] Uploading points to Qdrant container...")
    client.upsert(collection_name=collection_name, points=points)
    print(" Ingestion process completed successfully!")


if __name__ == "__main__":
    print("\n--- Testing Qdrant Initialization & Upload ---")


    try:
        upload_chunks_to_qdrant("./single_document/test.pdf")
        print("\n[!] Verify the data at: http://localhost:6333/dashboard")
    except Exception as e:
        print(f"[!] Error during upload to Qdrant: {e}")
