#!/usr/bin/env python3
"""
Extract hooks and filters from WordPress plugin PHP files.
Generates JSONL entries for the knowledge base.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional


class HookExtractor:
    """Extract WordPress hooks and filters from PHP files."""

    def __init__(self, plugin_path: str):
        self.plugin_path = Path(plugin_path)
        self.hooks = []

    def extract_from_php_files(self) -> List[Dict]:
        """Recursively extract hooks from all PHP files."""
        php_files = list(self.plugin_path.rglob("*.php"))
        print(f"Found {len(php_files)} PHP files")

        for php_file in php_files:
            try:
                with open(php_file, "r", errors="ignore") as f:
                    content = f.read()
                    self._extract_from_content(content, php_file.name)
            except Exception as e:
                print(f"Error reading {php_file}: {e}")

        return self.hooks

    def _extract_from_content(self, content: str, filename: str):
        """Extract hooks from PHP file content."""

        # Pattern for apply_filters and do_action calls
        filter_pattern = r"(?:apply_filters|do_action)\s*\(\s*['\"]([^'\"]+)['\"]"
        matches = re.finditer(filter_pattern, content)

        for match in matches:
            hook_name = match.group(1)

            # Find preceding comment/documentation
            start_pos = max(0, match.start() - 500)
            preceding = content[start_pos:match.start()]

            # Extract PHPDoc comment if available
            phpdoc = self._extract_phpdoc(preceding)

            if hook_name not in [h.get("name") for h in self.hooks]:
                hook_type = "filter" if "apply_filters" in content[match.start():match.end() + 20] else "action"

                hook_entry = {
                    "name": hook_name,
                    "type": hook_type,
                    "file": filename,
                    "description": phpdoc.get("description", f"{hook_type.title()} hook for {hook_name}"),
                    "params": phpdoc.get("params", []),
                }

                self.hooks.append(hook_entry)

    def _extract_phpdoc(self, preceding_text: str) -> Dict:
        """Extract PHPDoc comment information."""
        result = {"description": "", "params": []}

        # Look for PHPDoc comment
        phpdoc_match = re.search(r"/\*\*(.*?)\*/", preceding_text, re.DOTALL)
        if phpdoc_match:
            phpdoc_content = phpdoc_match.group(1)

            # Extract main description (lines without @)
            description_lines = []
            param_lines = []

            for line in phpdoc_content.split("\n"):
                line = line.strip().lstrip("*").strip()
                if line.startswith("@"):
                    param_lines.append(line)
                elif line and not line.startswith("@"):
                    description_lines.append(line)

            result["description"] = " ".join(description_lines)[:200]

            # Extract parameters
            for param_line in param_lines:
                if param_line.startswith("@param"):
                    # Extract parameter name
                    param_match = re.search(r"@param\s+(?:\$\w+|[\w|]+)\s+(\$?\w+)", param_line)
                    if param_match:
                        result["params"].append(param_match.group(1))

        return result

    def generate_jsonl(self, output_file: str, plugin_name: str = "Plugin"):
        """Generate JSONL knowledge base entries."""
        entries = []

        # Group hooks by type
        filters = [h for h in self.hooks if h["type"] == "filter"]
        actions = [h for h in self.hooks if h["type"] == "action"]

        # Create entries for each hook
        for i, hook in enumerate(self.hooks, start=1):
            entry = {
                "id": f"hook-{hook['type'][0]}-{i:03d}",
                "topic": f"{hook['type']}_hook",
                "source_type": "hook_documentation",
                "hook_name": hook["name"],
                "hook_type": hook["type"],
                "file": hook["file"],
                "keywords": [
                    hook["name"],
                    hook["type"],
                    "filter" if hook["type"] == "filter" else "action",
                    "hook",
                    "customize",
                    "extend",
                ] + hook.get("params", []),
                "content": f"""
Hook: {hook['name']}
Type: {hook['type'].upper()}
File: {hook['file']}
Description: {hook['description']}

Parameters: {', '.join(hook['params']) if hook['params'] else 'No parameters documented'}

Usage Example:
add_{hook['type']}('{hook['name']}', function($param) {{
    // Your custom code here
}});

This {hook['type']} allows you to customize the behavior of {hook['name'].replace('_', ' ')}.
""",
            }
            entries.append(entry)

        # Write to JSONL file
        with open(output_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        print(f"\n✓ Generated {len(entries)} hook entries")
        print(f"  - Filters: {len(filters)}")
        print(f"  - Actions: {len(actions)}")
        print(f"  - Output: {output_file}")

        return entries


def main():
    """Extract hooks from plugin and generate knowledge base."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_hooks.py <plugin_path> [output_file]")
        print("Example: python extract_hooks.py /path/to/plugin plugin-hooks.jsonl")
        sys.exit(1)

    plugin_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "plugin-hooks.jsonl"

    print(f"Extracting hooks from: {plugin_path}")

    extractor = HookExtractor(plugin_path)
    hooks = extractor.extract_from_php_files()

    print(f"\nFound {len(hooks)} unique hooks/filters")

    if hooks:
        extractor.generate_jsonl(output_file)
        print("\nHooks extracted successfully!")
    else:
        print("No hooks found. Check the plugin path.")


if __name__ == "__main__":
    main()
