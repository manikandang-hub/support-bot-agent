import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer, util
import torch


class RAGKnowledgeBase:
    """Lightweight RAG system using embeddings and semantic search."""

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        self.kb_dir = Path(knowledge_base_dir)

        # Initialize sentence transformer for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Store documents and embeddings per plugin
        self.plugin_docs: Dict[str, List[Dict]] = {}
        self.plugin_embeddings: Dict[str, torch.Tensor] = {}

        # Load all plugin knowledge bases
        self._load_all_knowledge_bases()

    def _load_all_knowledge_bases(self):
        """Load and index all plugin knowledge bases."""
        for plugin_dir in self.kb_dir.iterdir():
            if plugin_dir.is_dir():
                plugin_name = plugin_dir.name
                self._index_plugin(plugin_name, plugin_dir)

    def _index_plugin(self, plugin_name: str, plugin_dir: Path):
        """Index a single plugin's knowledge base."""
        documents = []

        try:
            # Index Markdown files (documentation)
            for md_file in plugin_dir.glob("*.md"):
                with open(md_file, "r") as f:
                    content = f.read()
                    # Split by headers for better chunking
                    chunks = self._chunk_markdown(content)
                    for chunk in chunks:
                        documents.append({
                            "content": chunk,
                            "source": md_file.name,
                            "type": "documentation",
                        })

            # Index hooks from hooks_list.json
            hooks_file = plugin_dir / "hooks_list.json"
            if hooks_file.exists():
                with open(hooks_file, "r") as f:
                    hooks_data = json.load(f)
                    for hook in hooks_data.get("hooks", []):
                        hook_text = f"""
Hook: {hook['name']}
Type: {hook['type']}
Description: {hook['description']}
Parameters: {', '.join(hook['params'])}
File: {hook['file']}
Example: {hook.get('example', '')}
"""
                        documents.append({
                            "content": hook_text,
                            "source": "hooks_list.json",
                            "type": "hook",
                            "hook_name": hook['name']
                        })

            # Create embeddings for all documents
            if documents:
                contents = [doc["content"] for doc in documents]
                embeddings = self.model.encode(contents, convert_to_tensor=True)

                self.plugin_docs[plugin_name] = documents
                self.plugin_embeddings[plugin_name] = embeddings

                print(f"✓ Indexed plugin '{plugin_name}' with {len(documents)} documents")

        except Exception as e:
            print(f"✗ Error indexing plugin '{plugin_name}': {e}")

    def _chunk_markdown(self, content: str, chunk_size: int = 400) -> List[str]:
        """Split markdown content into chunks by headers."""
        chunks = []
        current_chunk = ""

        lines = content.split("\n")
        for line in lines:
            current_chunk += line + "\n"

            # Split at headers or when chunk is large enough
            if (line.startswith("#") or len(current_chunk) > chunk_size) and current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return [c for c in chunks if len(c) > 50]  # Filter out too-small chunks

    def search(
        self,
        plugin_name: str,
        query: str,
        n_results: int = 3,
        threshold: float = 0.3
    ) -> List[Dict]:
        """
        Semantic search over plugin knowledge base using embeddings.

        Returns:
            List of relevant documents with scores
        """
        if plugin_name not in self.plugin_docs:
            return []

        try:
            # Encode the query
            query_embedding = self.model.encode(query, convert_to_tensor=True)

            # Compute similarities
            documents = self.plugin_docs[plugin_name]
            embeddings = self.plugin_embeddings[plugin_name]

            similarities = util.pytorch_cos_sim(query_embedding, embeddings)[0]

            # Get top results
            top_k = min(n_results, len(documents))
            top_results = torch.topk(similarities, k=top_k)

            results = []
            for score, idx in zip(top_results.values, top_results.indices):
                similarity = float(score)

                if similarity > threshold:
                    doc = documents[idx]
                    results.append({
                        "content": doc["content"],
                        "similarity": similarity,
                        "source": doc.get("source"),
                        "type": doc.get("type"),
                    })

            return results

        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []

    def get_hook_names(self, plugin_name: str) -> List[str]:
        """Get all available hook names for a plugin."""
        if plugin_name not in self.plugin_docs:
            return []

        hook_names = []
        for doc in self.plugin_docs[plugin_name]:
            if doc.get("type") == "hook" and "hook_name" in doc:
                hook_names.append(doc["hook_name"])

        return hook_names
