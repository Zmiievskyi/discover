"""
Vector database module for semantic search.
Uses ChromaDB with OpenAI embeddings API for AI-powered search.
"""

import chromadb
from chromadb.config import Settings
from openai import OpenAI
from typing import List, Dict, Optional
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class VectorStore:
    """
    Class for working with ChromaDB vector database.
    Enables semantic search using OpenAI embeddings API.
    """

    def __init__(self,
                 persist_directory: str = './chroma_db',
                 collection_name: str = 'crawled_pages',
                 embedding_model: str = 'text-embedding-3-small',
                 api_key: Optional[str] = None):
        """
        Initialize ChromaDB vector store with OpenAI embeddings.

        Args:
            persist_directory: Directory to store ChromaDB data
            collection_name: Name of the ChromaDB collection
            embedding_model: OpenAI embedding model
                           Default: 'text-embedding-3-small' (1536-dim, $0.02/1M tokens)
                           Alternative: 'text-embedding-3-large' (3072-dim, $0.13/1M tokens, better quality)
            api_key: OpenAI API key (if not provided, will use OPENAI_API_KEY env variable)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

        # Verify API key is set
        if not self.openai_client.api_key:
            raise ValueError(
                "OpenAI API key not found! Set OPENAI_API_KEY environment variable or pass api_key parameter.\n"
                "Get your API key at: https://platform.openai.com/api-keys"
            )

        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

        print(f"✓ Vector store initialized: {persist_directory}")
        print(f"✓ Using OpenAI model: {embedding_model}")
        print(f"✓ Collection: {collection_name} (Documents: {self.collection.count()})")

    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL using hash"""
        return hashlib.md5(url.encode()).hexdigest()

    def _create_embedding(self, text: str) -> List[float]:
        """
        Create embedding using OpenAI API.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats)
        """
        try:
            # Truncate very long texts (OpenAI has 8191 token limit for text-embedding-3-small)
            # Roughly 4 chars = 1 token, so ~32000 chars max
            max_chars = 30000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."

            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )

            return response.data[0].embedding

        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            raise

    def add_page(self, url: str, title: str, content: str, metadata: Optional[Dict] = None):
        """
        Add page to vector database with embeddings.

        Args:
            url: Page URL (used as unique identifier)
            title: Page title
            content: Full page text
            metadata: Additional metadata to store
        """
        try:
            # Create document text combining title and content for better search
            document_text = f"{title}\n\n{content}"

            # Prepare metadata
            page_metadata = {
                'url': url,
                'title': title,
                'text_length': len(content)
            }
            if metadata:
                page_metadata.update(metadata)

            # Generate ID from URL
            doc_id = self._generate_id(url)

            # Create embedding using OpenAI API
            embedding = self._create_embedding(document_text)

            # Add to ChromaDB
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],  # Store full content
                metadatas=[page_metadata]
            )

            return True

        except Exception as e:
            print(f"Vector store add error: {e}")
            return False

    def add_pages_batch(self, pages: List[Dict]):
        """
        Add multiple pages at once (more efficient).

        Args:
            pages: List of page dictionaries with keys: url, title, content, metadata
        """
        if not pages:
            return

        try:
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            print(f"Generating embeddings for {len(pages)} pages using OpenAI API...")

            for i, page in enumerate(pages, 1):
                url = page['url']
                title = page.get('title', '')
                content = page.get('content', '')
                metadata = page.get('metadata', {})

                # Create document text
                document_text = f"{title}\n\n{content}"

                # Prepare metadata
                page_metadata = {
                    'url': url,
                    'title': title,
                    'text_length': len(content)
                }
                page_metadata.update(metadata)

                # Generate embedding
                try:
                    embedding = self._create_embedding(document_text)

                    ids.append(self._generate_id(url))
                    embeddings.append(embedding)
                    documents.append(content)
                    metadatas.append(page_metadata)

                    print(f"  [{i}/{len(pages)}] Embedded: {title[:50]}...")

                except Exception as e:
                    print(f"  [{i}/{len(pages)}] Failed to embed {url}: {e}")
                    continue

            # Batch add to ChromaDB
            if ids:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )

                print(f"✓ Added {len(ids)} pages to vector store")

        except Exception as e:
            print(f"Batch add error: {e}")

    def semantic_search(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Perform semantic search using natural language query.

        Args:
            query: Search query in natural language (e.g., "find all about security")
            top_k: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {'url': {'$contains': 'wiki'}})

        Returns:
            List of dictionaries with keys: url, title, content, distance, metadata
        """
        try:
            # Generate query embedding using OpenAI API
            query_embedding = self._create_embedding(query)

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata  # Optional metadata filtering
            )

            # Format results
            formatted_results = []
            if results and results['ids']:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'distance': results['distances'][0][i],
                        'metadata': results['metadatas'][0][i]
                    }
                    formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def delete_page(self, url: str):
        """Delete page from vector store by URL"""
        try:
            doc_id = self._generate_id(url)
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False

    def clear_all(self):
        """Clear all documents from collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print("✓ Vector store cleared")
            return True
        except Exception as e:
            print(f"Clear error: {e}")
            return False

    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection_name,
            'persist_directory': self.persist_directory,
            'embedding_model': self.embedding_model
        }
