import json
from typing import Optional
from anthropic import Anthropic
from openai import OpenAI

from app.hooks_validator import HooksValidator
from app.knowledge_base_loader import KnowledgeBaseLoader


class CodeGenerator:
    """Generates PHP code snippets using Claude API or OpenAI API."""

    def __init__(
        self,
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        knowledge_base_dir: str = "knowledge_base",
        provider: str = "auto"
    ):
        self.validator = HooksValidator(knowledge_base_dir)
        self.kb_loader = KnowledgeBaseLoader(knowledge_base_dir)
        self.mock_mode = False
        self.provider = provider
        self.anthropic_client = None
        self.openai_client = None

        # Determine which provider to use
        if provider == "auto":
            if openai_key and not openai_key.startswith("sk-demo"):
                self.provider = "openai"
            elif anthropic_key and not anthropic_key.startswith("sk-ant-demo"):
                self.provider = "anthropic"
            else:
                self.mock_mode = True
        elif provider == "openai" and openai_key:
            self.provider = "openai"
        elif provider == "anthropic" and anthropic_key:
            self.provider = "anthropic"
        else:
            self.mock_mode = True

        # Initialize clients
        if not self.mock_mode:
            if self.provider == "anthropic" and anthropic_key:
                self.anthropic_client = Anthropic(api_key=anthropic_key)
            elif self.provider == "openai" and openai_key:
                self.openai_client = OpenAI(api_key=openai_key)

    def generate_solution(
        self,
        plugin_id: str,
        plugin_name: str,
        query: str,
        available_hooks: list[str],
        conversation_context: str = "",
    ) -> dict:
        """
        Generate a code solution for the customer query.

        Args:
            plugin_id: Plugin identifier
            plugin_name: Human-readable plugin name
            query: Customer's question
            available_hooks: List of available hooks for the plugin
            conversation_context: Previous messages/snippets for follow-up questions

        Returns dict with:
        - action: "snippet" or "escalate"
        - explanation: explanation text
        - code: generated PHP code (if snippet)
        - hook_names: list of hooks used
        - needs_escalation: whether to escalate
        - reason: escalation reason if applicable
        """

        # Mock mode for testing without real API key
        if self.mock_mode:
            return self._generate_mock_solution(plugin_id, plugin_name, query, available_hooks)

        hooks_list = ", ".join(available_hooks[:10])  # Top 10 for context

        # Get context from knowledge base (increased to 5 to capture row-level hooks)
        kb_context = self.kb_loader.get_context_for_query(plugin_id, query, max_results=5)

        # Build prompt with conversation context for follow-ups
        conversation_section = ""
        is_followup = False
        if conversation_context:
            is_followup = True
            conversation_section = f"""
═══════════════════════════════════════════════════════════════
PREVIOUS CONVERSATION (VERY IMPORTANT - READ CAREFULLY):
═══════════════════════════════════════════════════════════════
{conversation_context}

═══════════════════════════════════════════════════════════════
⚠️ CRITICAL INSTRUCTIONS FOR THIS FOLLOW-UP QUESTION:
═══════════════════════════════════════════════════════════════
1. THIS IS A FOLLOW-UP QUESTION - Customer is modifying their previous request
2. READ the previous code snippet above - that is your BASE
3. IDENTIFY the hook used in previous code (e.g., wt_batch_product_export_row_data_google)
4. If customer asks for "different channel" (facebook, pinterest, etc.):
   → Replace ONLY the channel name in the hook (google → facebook)
   → Keep ALL the logic/code structure EXACTLY the same
   → Example: wt_batch_product_export_row_data_google → wt_batch_product_export_row_data_facebook
5. DO NOT create new code - COPY and MODIFY the previous code
6. Return the COMPLETE modified code (not just the changes)

EXAMPLE OF CORRECT MODIFICATION:
   Previous: add_filter('wt_batch_product_export_row_data_google', ...
   Follow-up: "I need this for facebook"
   Correct: add_filter('wt_batch_product_export_row_data_facebook', ... (WITH SAME LOGIC)
"""

        prompt = f"""🚨 INSTRUCTIONS - READ FIRST BEFORE ANYTHING ELSE 🚨
{conversation_section if conversation_section else ""}

═══════════════════════════════════════════════════════════════
You are SupportBot, an expert AI support agent for the WordPress plugin "{plugin_name}".
═══════════════════════════════════════════════════════════════

The customer is asking about customizing this plugin.

KNOWLEDGE BASE & AVAILABLE HOOKS:
{kb_context}

Additional hooks available: {hooks_list}

IMPORTANT RULES:
1. FIRST: Check the knowledge base context above for relevant hooks and examples that match the customer's needs.
2. You can suggest ANY hook mentioned in the knowledge base OR in the hooks list. If the customer's needs cannot be met with these hooks, respond with action="escalate".
3. ALWAYS respond ONLY with valid JSON - nothing else, no markdown, no code blocks.
4. If you suggest code, it MUST be syntactically correct PHP that uses hooks from the knowledge base or hooks list.
5. Provide explanations that reference the specific hook being used.
6. {"FOR FOLLOW-UP QUESTIONS (if there is previous conversation history above):" if is_followup else "If there is follow-up questions later:"}
   - MODIFY the previous code snippet, do NOT create entirely new code
   - If customer asks for "same but for [channel]", change the hook name from wt_batch_product_export_row_data_google to wt_batch_product_export_row_data_[channel] but KEEP the logic
   - Preserve all the previous logic and only add/change what was requested
   - Show the COMPLETE modified code with all original + new changes

Customer Question: {query}

RESPOND WITH THIS JSON STRUCTURE (and ONLY this JSON):
{{"action": "snippet" or "escalate", "explanation": "Clear explanation of how the hook solves the problem", "code": "<?php ... code here ...", "needs_plugin_change": false, "reason": "reason if escalating"}}

Return ONLY the JSON object, no other text."""

        # Call appropriate LLM provider
        if self.provider == "openai":
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.choices[0].message.content
        else:  # anthropic
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text

        # Parse JSON response - with better error handling
        try:
            # Clean up response text (remove markdown code blocks if present)
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            result = json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            # Log the problematic response for debugging
            print(f"JSON Parse Error: {e}")
            print(f"Response was: {response_text[:200]}")
            return {
                "action": "escalate",
                "explanation": "Unable to parse response. Please contact support.",
                "needs_escalation": True,
                "reason": f"response_parsing_error: {str(e)[:50]}",
            }

        # Validate hooks if code was generated
        if result.get("action") == "snippet" and result.get("code"):
            is_valid, invalid_hooks = self.validator.validate_hooks(
                plugin_id, result["code"]
            )
            if not is_valid:
                return {
                    "action": "escalate",
                    "explanation": f"The solution requires hooks not available in {plugin_name}. Please contact our support team for custom development.",
                    "needs_escalation": True,
                    "reason": f"invalid_hooks: {', '.join(invalid_hooks)}",
                }

            # Extract actual hooks used
            used_hooks = self.validator.extract_hooks_from_code(result["code"])
            result["hook_names"] = sorted(list(used_hooks))

        return result

    def _generate_mock_solution(
        self,
        plugin_id: str,
        plugin_name: str,
        query: str,
        available_hooks: list[str],
    ) -> dict:
        """Generate a mock solution for testing without API key."""
        mock_solutions = {
            "product-feed": {
                "filter": {
                    "action": "snippet",
                    "explanation": "You can filter products before export using the `wt_product_feed_filter_product` hook. This hook runs for each product and allows you to modify the product data before it's added to the feed.",
                    "code": """<?php
// Add this code to your theme's functions.php or a custom plugin

add_filter('wt_product_feed_filter_product', function($product_data, $product) {
    // Modify product data before export
    $product_data['name'] = 'Custom: ' . $product_data['name'];

    // You can also modify price, description, etc.
    $product_data['price'] = $product->get_price() * 1.1; // 10% markup

    return $product_data;
}, 10, 2);""",
                    "hook_names": ["wt_product_feed_filter_product"],
                    "needs_plugin_change": False,
                },
                "skip": {
                    "action": "snippet",
                    "explanation": "Use the `wt_product_feed_skip_product` hook to exclude certain products from the feed based on custom conditions.",
                    "code": """<?php
// Skip products below a certain price or with specific status

add_filter('wt_product_feed_skip_product', function($skip, $product) {
    // Skip products with less than 5 reviews
    if ($product->get_review_count() < 5) {
        return true;
    }

    // Skip out-of-stock products
    if (!$product->is_in_stock()) {
        return true;
    }

    return $skip;
}, 10, 2);""",
                    "hook_names": ["wt_product_feed_skip_product"],
                    "needs_plugin_change": False,
                }
            },
            "invoice-plugin": {
                "customize": {
                    "action": "snippet",
                    "explanation": "Customize invoice content using the `wt_invoice_content` hook. This allows you to add company branding, custom headers/footers, or modify the layout.",
                    "code": """<?php
// Customize invoice HTML content

add_filter('wt_invoice_content', function($html, $invoice) {
    // Add custom header
    $custom_header = '<div style="text-align: center; margin-bottom: 20px;">';
    $custom_header .= '<h2>INVOICE</h2>';
    $custom_header .= '<p style="color: #666;">Thank you for your business!</p>';
    $custom_header .= '</div>';

    // Prepend header to invoice
    return $custom_header . $html;
}, 10, 2);""",
                    "hook_names": ["wt_invoice_content"],
                    "needs_plugin_change": False,
                },
                "totals": {
                    "action": "snippet",
                    "explanation": "Modify invoice totals (subtotal, tax, shipping) using the `wt_invoice_totals` hook. Useful for applying custom discounts or adjustments.",
                    "code": """<?php
// Modify invoice totals

add_filter('wt_invoice_totals', function($totals, $invoice) {
    // Apply a 5% loyalty discount
    $subtotal = $totals['subtotal'];
    $loyalty_discount = $subtotal * 0.05;

    $totals['subtotal'] -= $loyalty_discount;
    $totals['total'] -= $loyalty_discount;

    return $totals;
}, 10, 2);""",
                    "hook_names": ["wt_invoice_totals"],
                    "needs_plugin_change": False,
                }
            }
        }

        # Determine which mock response to return based on query keywords
        keywords_filter = ["filter", "exclude", "skip", "condition", "custom meta"]
        keywords_customize = ["customize", "modify", "header", "footer", "branding", "style"]
        keywords_totals = ["total", "discount", "price", "adjust", "subtotal", "tax"]

        query_lower = query.lower()

        # Select appropriate mock response
        solution = None
        if plugin_id == "product-feed":
            if any(kw in query_lower for kw in keywords_filter + ["product", "meta field"]):
                solution = mock_solutions["product-feed"]["filter"]
            elif any(kw in query_lower for kw in keywords_filter):
                solution = mock_solutions["product-feed"]["skip"]
            else:
                solution = mock_solutions["product-feed"]["filter"]

        elif plugin_id == "invoice-plugin":
            if any(kw in query_lower for kw in keywords_customize):
                solution = mock_solutions["invoice-plugin"]["customize"]
            elif any(kw in query_lower for kw in keywords_totals):
                solution = mock_solutions["invoice-plugin"]["totals"]
            else:
                solution = mock_solutions["invoice-plugin"]["customize"]

        return solution if solution else {
            "action": "snippet",
            "explanation": "✨ Demo mode: This is a mock response for testing. Add a real ANTHROPIC_API_KEY to generate actual solutions.",
            "code": "<?php\n// Mock demo code\necho 'Demo response - add real API key to get actual solutions';",
            "hook_names": [],
            "needs_plugin_change": False,
        }
