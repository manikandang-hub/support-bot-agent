#!/usr/bin/env python3
"""
Merge extracted hooks from JSONL into hooks_list.json
"""

import json
from pathlib import Path
from typing import List, Dict


def merge_hooks(jsonl_file: str, output_file: str, min_length: int = 3):
    """
    Convert JSONL extracted hooks into hooks_list.json format.

    Args:
        jsonl_file: Path to extracted hooks JSONL file
        output_file: Path to output hooks_list.json
        min_length: Minimum length for hook name to be considered valid
    """
    hooks = []
    seen_names = set()

    print(f"Reading hooks from: {jsonl_file}")

    try:
        with open(jsonl_file, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    hook_name = entry.get("hook_name", "").strip()

                    # Filter out invalid hook names
                    if (
                        hook_name
                        and len(hook_name) > min_length
                        and "{" not in hook_name  # Skip template variables
                        and "$" not in hook_name  # Skip PHP variables
                        and hook_name not in seen_names
                    ):
                        hook = {
                            "name": hook_name,
                            "type": entry.get("hook_type", "filter"),
                            "params": entry.get("params", entry.get("keywords", [])),
                            "description": entry.get("description", "")[:200].strip(),
                            "file": entry.get("file", ""),
                        }

                        hooks.append(hook)
                        seen_names.add(hook_name)

        print(f"Found {len(hooks)} valid hooks")

        # Create hooks_list.json structure
        output_data = {
            "hooks": hooks,
            "total": len(hooks),
            "source": "Extracted from plugin PHP files",
        }

        # Write output file
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Generated {output_file}")
        print(f"  - Total hooks: {len(hooks)}")
        print(f"  - Filters: {len([h for h in hooks if h['type'] == 'filter'])}")
        print(f"  - Actions: {len([h for h in hooks if h['type'] == 'action'])}")

        # Show sample
        print("\nSample hooks:")
        for hook in hooks[:5]:
            print(f"  - {hook['name']} ({hook['type']})")

    except Exception as e:
        print(f"Error: {e}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python merge_hooks.py <jsonl_file> [output_file]")
        sys.exit(1)

    jsonl_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "hooks_list.json"

    merge_hooks(jsonl_file, output_file)


if __name__ == "__main__":
    main()
