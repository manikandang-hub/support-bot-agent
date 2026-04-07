import json
import regex as re
from typing import List, Set
from pathlib import Path


class HooksValidator:
    """Validates hooks used in generated code against known plugin hooks."""

    # WordPress core hooks that are allowed in solutions
    # These are standard WordPress/WooCommerce hooks used for integrations
    WORDPRESS_CORE_HOOKS = {
        "template_redirect",
        "wp_loaded",
        "init",
        "wp_enqueue_scripts",
        "wp_footer",
        "wp_head",
        "admin_init",
        "admin_enqueue_scripts",
        "woocommerce_init",
        "woocommerce_cart_loaded_from_session",
        "woocommerce_before_checkout_form",
        "woocommerce_after_checkout_form",
        "woocommerce_checkout_process",
        "wp_safe_remote_get",
        "wp_redirect",
        "wc_get_product",
        "WC_Cart",
        "is_cart",
        "is_checkout",
    }

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        self.kb_dir = Path(knowledge_base_dir)
        self.plugin_hooks: dict[str, Set[str]] = {}
        self._load_hooks()

    def _load_hooks(self):
        """Load hooks from hooks_list.json for each plugin."""
        for plugin_dir in self.kb_dir.iterdir():
            if plugin_dir.is_dir():
                hooks_file = plugin_dir / "hooks_list.json"
                if hooks_file.exists():
                    with open(hooks_file) as f:
                        data = json.load(f)
                        hook_names = {hook["name"] for hook in data.get("hooks", [])}
                        self.plugin_hooks[plugin_dir.name] = hook_names

    def extract_hooks_from_code(self, code: str) -> Set[str]:
        """Extract hook names from PHP code using regex."""
        hooks = set()

        # Pattern: add_action('hook_name', ...) or add_filter('hook_name', ...)
        action_pattern = r"(?:add_action|add_filter)\s*\(\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(action_pattern, code)
        hooks.update(matches)

        # Pattern: apply_filters('hook_name', ...) or do_action('hook_name', ...)
        execute_pattern = r"(?:apply_filters|do_action)\s*\(\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(execute_pattern, code)
        hooks.update(matches)

        return hooks

    def validate_hooks(self, plugin_id: str, code: str) -> tuple[bool, List[str]]:
        """
        Validate that all hooks in generated code exist in the plugin or are WordPress core hooks.

        Returns:
            (is_valid, invalid_hooks)
        """
        if plugin_id not in self.plugin_hooks:
            # Plugin not found in knowledge base - escalate for safety
            return False, ["unknown_plugin"]

        used_hooks = self.extract_hooks_from_code(code)
        available_hooks = self.plugin_hooks[plugin_id]

        # Filter out WordPress core hooks - they're always valid
        # Only keep hooks that are neither in plugin hooks nor in core WordPress hooks
        invalid_hooks = used_hooks - available_hooks - self.WORDPRESS_CORE_HOOKS

        return len(invalid_hooks) == 0, list(invalid_hooks)

    def get_available_hooks(self, plugin_id: str) -> List[str]:
        """Get list of available hooks for a plugin."""
        return sorted(list(self.plugin_hooks.get(plugin_id, set())))
