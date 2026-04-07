"""
Semantic RAG using Chroma DB and sentence embeddings.
Provides semantic search over knowledge base documents.
"""

import json
import chromadb
from pathlib import Path
from typing import List, Dict


class SemanticRAG:
    """Semantic search over knowledge base using embeddings."""

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        """Initialize Chroma DB with knowledge base documents."""
        self.kb_dir = Path(knowledge_base_dir)

        # Initialize Chroma client (persistent storage)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.kb_dir / ".chroma_db")
        )

        # Collections per plugin
        self.collections: Dict[str, any] = {}
        self._load_knowledge_bases()

    def _load_knowledge_bases(self):
        """Load JSONL files and index them in Chroma."""
        for plugin_dir in self.kb_dir.iterdir():
            if plugin_dir.is_dir() and plugin_dir.name != ".chroma_db":
                plugin_name = plugin_dir.name
                jsonl_files = list(plugin_dir.glob("*.jsonl"))

                if jsonl_files:
                    # Get or create collection for this plugin
                    collection_name = f"plugin_{plugin_name}"

                    try:
                        # Delete existing collection to refresh
                        self.chroma_client.delete_collection(name=collection_name)
                    except:
                        pass  # Collection doesn't exist yet

                    collection = self.chroma_client.get_or_create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )

                    # Load and index documents
                    doc_count = 0
                    for jsonl_file in jsonl_files:
                        try:
                            with open(jsonl_file, "r") as f:
                                for line in f:
                                    if line.strip():
                                        doc = json.loads(line)

                                        # Create unique ID
                                        doc_id = doc.get("id", f"doc_{doc_count}")

                                        # Combine content for embedding
                                        text = f"{doc.get('topic', '')} {doc.get('content', '')}"

                                        # Add to collection
                                        collection.add(
                                            ids=[doc_id],
                                            documents=[text],
                                            metadatas=[{
                                                "topic": doc.get("topic", ""),
                                                "source": str(jsonl_file.name),
                                                "hook_name": doc.get("hook_name", ""),
                                            }]
                                        )
                                        doc_count += 1

                            print(f"✓ Indexed {doc_count} documents from {plugin_name}/{jsonl_file.name}")
                        except Exception as e:
                            print(f"✗ Error indexing {jsonl_file}: {e}")

                    self.collections[plugin_name] = collection

    def search(
        self,
        plugin_name: str,
        query: str,
        n_results: int = 5,
    ) -> List[Dict]:
        """
        Semantic search using embeddings.

        Args:
            plugin_name: Plugin identifier
            query: Search query
            n_results: Number of results to return

        Returns:
            List of matching documents with metadata
        """
        if plugin_name not in self.collections:
            return []

        collection = self.collections[plugin_name]

        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            if not results or not results["ids"] or not results["ids"][0]:
                return []

            # Convert Chroma results to document format
            documents = []
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                # Chroma uses cosine distance (0-2), convert to similarity (0-1)
                similarity = 1 - (distance / 2)

                documents.append({
                    "id": doc_id,
                    "topic": metadata.get("topic", ""),
                    "hook_name": metadata.get("hook_name", ""),
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "similarity": similarity,
                    "source": metadata.get("source", ""),
                })

            return documents
        except Exception as e:
            print(f"✗ Search error: {e}")
            return []

    def get_context_for_query(
        self,
        plugin_name: str,
        query: str,
        max_results: int = 5,
    ) -> str:
        """
        Get formatted context from semantic search for LLM.

        Args:
            plugin_name: Plugin identifier
            query: Search query
            max_results: Maximum results to include

        Returns:
            Formatted context string for LLM
        """
        results = self.search(plugin_name, query, n_results=max_results)

        print(f"   📚 Knowledge Base Search Results (Semantic):")
        print(f"      Query: '{query[:50]}...'")
        print(f"      Results found: {len(results)}/{max_results}")

        if not results:
            print(f"      No relevant documents found")
            return ""

        print(f"      Documents used for context:")
        for i, doc in enumerate(results, 1):
            topic = doc.get("topic", "Unknown")
            similarity = doc.get("similarity", 0)
            print(f"        {i}. Topic: {topic} (similarity: {similarity:.2f})")

        context = "\n\nRELEVANT KNOWLEDGE BASE (Semantic Search):\n"
        for i, doc in enumerate(results, 1):
            topic = doc.get("topic", "Unknown").replace("_", " ").title()
            # Include more content (3000 chars) to ensure complete solutions are passed to LLM
            content = doc.get("content", "")[:3000]
            context += f"\n{i}. {topic}\n{content}...\n"

        return context
