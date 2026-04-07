import json
from pathlib import Path
from typing import List, Dict, Optional


class KnowledgeBaseLoader:
    """Load and search JSONL knowledge base files."""

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        self.kb_dir = Path(knowledge_base_dir)
        self.plugin_kb: Dict[str, List[Dict]] = {}
        self._load_all_knowledge_bases()

    def _load_all_knowledge_bases(self):
        """Load all JSONL knowledge base files."""
        for plugin_dir in self.kb_dir.iterdir():
            if plugin_dir.is_dir():
                plugin_name = plugin_dir.name
                jsonl_files = list(plugin_dir.glob("*.jsonl"))

                if jsonl_files:
                    docs = []
                    for jsonl_file in jsonl_files:
                        try:
                            with open(jsonl_file, "r") as f:
                                for line in f:
                                    if line.strip():
                                        doc = json.loads(line)
                                        docs.append(doc)
                            print(f"✓ Loaded {len(docs)} documents from {plugin_name}/{jsonl_file.name}")
                        except Exception as e:
                            print(f"✗ Error loading {jsonl_file}: {e}")

                    if docs:
                        self.plugin_kb[plugin_name] = docs

    def search(
        self,
        plugin_name: str,
        query: str,
        n_results: int = 3,
    ) -> List[Dict]:
        """
        Simple keyword-based search over knowledge base.
        Returns top matching documents based on keyword overlap.
        """
        if plugin_name not in self.plugin_kb:
            return []

        docs = self.plugin_kb[plugin_name]
        query_words = set(query.lower().split())

        # Score each document based on keyword matches
        scored_docs = []
        for doc in docs:
            keywords = set(k.lower() for k in doc.get("keywords", []))
            matches = len(query_words & keywords)

            if matches > 0:
                scored_docs.append({
                    "score": matches,
                    "doc": doc,
                })

        # Sort by score and return top results
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in scored_docs[:n_results]]

    def get_context_for_query(
        self,
        plugin_name: str,
        query: str,
        max_results: int = 3,
    ) -> str:
        """
        Get formatted context from knowledge base for the query.
        """
        results = self.search(plugin_name, query, n_results=max_results)

        print(f"   📚 Knowledge Base Search Results:")
        print(f"      Query: '{query[:50]}...'")
        print(f"      Results found: {len(results)}/{max_results}")

        if not results:
            print(f"      No relevant documents found")
            return ""

        print(f"      Documents used for context:")
        for i, doc in enumerate(results, 1):
            topic = doc.get("topic", "Unknown")
            hook_name = doc.get("hook_name", "N/A")
            print(f"        {i}. Topic: {topic}, Hook: {hook_name}")

        context = "\n\nRELEVANT KNOWLEDGE BASE:\n"
        for i, doc in enumerate(results, 1):
            topic = doc.get("topic", "Unknown").replace("_", " ").title()
            content = doc.get("content", "")[:800]  # First 800 chars for more context
            context += f"\n{i}. {topic}\n{content}...\n"

        return context
