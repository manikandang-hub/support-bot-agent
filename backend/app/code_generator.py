import json
from typing import Optional
from anthropic import Anthropic
from openai import OpenAI

from app.hooks_validator import HooksValidator
from app.semantic_rag import SemanticRAG


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
        self.rag = SemanticRAG(knowledge_base_dir)  # Use semantic RAG instead
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

        print("\n" + "=" * 80)
        print("🔍 CODE GENERATION FLOW - STEP BY STEP LOGGING")
        print("=" * 80)

        print(f"\n1️⃣  QUERY RECEIVED:")
        print(f"   Plugin: {plugin_name} ({plugin_id})")
        print(f"   Customer Question: {query[:100]}...")
        print(f"   Is Follow-up: {bool(conversation_context)}")

        hooks_list = ", ".join(available_hooks[:10])  # Top 10 for context
        print(f"\n2️⃣  AVAILABLE HOOKS (Top 10 for LLM context):")
        print(f"   Total hooks: {len(available_hooks)}")
        print(f"   Sample: {hooks_list[:80]}...")

        # Get context from knowledge base using semantic search
        print(f"\n3️⃣  SEARCHING KNOWLEDGE BASE (Semantic RAG):")
        kb_context = self.rag.get_context_for_query(plugin_id, query, max_results=5)
        print(f"   Searching for: '{query[:60]}...'")
        print(f"   Max results: 5")
        print(f"   Knowledge base documents found")
        print(f"   Context length: {len(kb_context)} characters")

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
🚨 CRITICAL INSTRUCTIONS FOR THIS FOLLOW-UP QUESTION:
═══════════════════════════════════════════════════════════════
1. THIS IS A FOLLOW-UP QUESTION - Customer is modifying their previous request
2. READ the previous code snippet above - that is your BASE CODE
3. IDENTIFY the EXACT hook name used in previous code
   Example: wt_batch_product_export_row_data_google
4. CHECK THE CUSTOMER'S FOLLOW-UP REQUEST:
   - If they ask for a DIFFERENT CHANNEL/PLATFORM (facebook, pinterest, twitter, tiktok, bing, etc.):
     ✓ DO THIS: Replace the channel name in the hook ONLY
     ✓ KEEP all logic/structure EXACTLY the same
     ✓ Example: google → facebook means:
       FROM: add_filter('wt_batch_product_export_row_data_google', ...
       TO:   add_filter('wt_batch_product_export_row_data_facebook', ...
   - If they ask for the SAME code:
     ✓ Return the exact same code without modification
5. ABSOLUTELY DO NOT:
   ✗ Return the old hook name (that's wrong!)
   ✗ Create completely new code
   ✗ Forget to change the hook name
6. Return the COMPLETE modified code snippet

VERIFICATION CHECKLIST (BEFORE YOU RESPOND):
☐ Did I change the hook name from the previous version?
☐ Is the hook name in the add_filter() call updated?
☐ Is the logic/loop structure identical to the previous code?
☐ Does the code match the customer's channel request?

EXAMPLE - WHAT CORRECT MODIFICATION LOOKS LIKE:
   Previous code had:   add_filter('wt_batch_product_export_row_data_google', ...
   Customer says:       "I need this for facebook"
   Your response should have: add_filter('wt_batch_product_export_row_data_facebook', ... (WITH IDENTICAL LOGIC)
   Your response should NOT have: add_filter('wt_batch_product_export_row_data_google', ... (WRONG!)
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

IMPORTANT RULES - READ AND FOLLOW EXACTLY:
1. 🚨 CRITICAL: PRIORITY ORDER FOR CODE GENERATION:
   A. FIRST: Search the knowledge base context above for code that addresses the customer's question
   B. If found: EXTRACT AND USE that code EXACTLY (with only minimal channel/variation changes if requested)
   C. If NOT found: Only then generate new code from available hooks
   D. NEVER generate new code if knowledge base has a similar example - extract and modify it instead

2. When extracting code from knowledge base:
   - Copy the PHP code snippet exactly as shown
   - Only change hook names if customer asks for a different channel (e.g., facebook → google)
   - Keep the logic and structure identical
   - Include the PHPDoc comments and escaping exactly as shown

3. You can suggest ANY hook from the knowledge base OR hooks list. If not possible, respond with action="escalate".

4. ALWAYS respond ONLY with valid JSON - nothing else, no markdown, no code blocks.

5. Provide clear explanations that reference which knowledge base entry or hook was used.
6. {"FOR FOLLOW-UP QUESTIONS (if there is previous conversation history above):" if is_followup else "If there is follow-up questions later:"}
   - MODIFY the previous code snippet, do NOT create entirely new code
   - If customer asks for "same but for [channel]", change the hook name from wt_batch_product_export_row_data_google to wt_batch_product_export_row_data_[channel] but KEEP the logic
   - Preserve all the previous logic and only add/change what was requested
   - Show the COMPLETE modified code with all original + new changes

WORDPRESS CODING STANDARDS (MUST FOLLOW):
- Use 4 spaces for indentation (not tabs)
- Function names: snake_case (e.g., custom_meta_checkout_url)
- Variable names: snake_case (e.g., $product_id, $checkout_link)
- Add PHPDoc comments for functions:
  /**
   * Brief description of what the function does.
   *
   * @param type $param_name Description
   * @return type Description
   */
- Always escape output with esc_url(), esc_html(), esc_attr() when needed
- Always sanitize input with sanitize_text_field(), intval(), etc when needed
- Use WordPress functions: home_url(), get_option(), etc instead of raw PHP
- Proper spacing: space before opening brace, space around operators
- Always include full <?php opening tag and proper closing if needed

Customer Question: {query}

RESPOND WITH THIS JSON STRUCTURE (and ONLY this JSON):
{{"action": "snippet" or "escalate", "explanation": "Clear explanation of how the hook solves the problem", "code": "<?php ... code here ...", "needs_plugin_change": false, "reason": "reason if escalating"}}

Return ONLY the JSON object, no other text."""

        print(f"\n4️⃣  CONVERSATION CONTEXT:")
        if conversation_context:
            print(f"   This is a follow-up question")
            print(f"   Previous context length: {len(conversation_context)} characters")
            print(f"   Will be included in LLM prompt")
        else:
            print(f"   New conversation (no previous context)")

        print(f"\n5️⃣  BUILDING LLM PROMPT:")
        print(f"   Provider: {self.provider.upper()}")
        print(f"   Model: {'gpt-4-turbo' if self.provider == 'openai' else 'claude-3-5-sonnet-20241022'}")
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Max tokens: 2000")

        # Call appropriate LLM provider
        print(f"\n6️⃣  CALLING LLM API...")
        if self.provider == "openai":
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.choices[0].message.content
            print(f"   ✓ OpenAI API called successfully")
        else:  # anthropic
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text
            print(f"   ✓ Anthropic API called successfully")

        print(f"   Response length: {len(response_text)} characters")
        print(f"   Response preview: {response_text[:300]}...")

        # Parse JSON response - with better error handling
        print(f"\n7️⃣  PARSING LLM RESPONSE:")
        try:
            # Clean up response text (remove markdown code blocks if present)
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
                print(f"   Removed ```json wrapper")
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
                print(f"   Removed ``` wrapper")
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                print(f"   Removed closing ``` wrapper")

            result = json.loads(cleaned.strip())
            print(f"   ✓ JSON parsed successfully")
            print(f"   - Action: {result.get('action')}")
            print(f"   - Has code: {bool(result.get('code'))}")
            if result.get('code'):
                print(f"   - Code length: {len(result['code'])} characters")
                print(f"   - Code lines: {len(result['code'].split(chr(10)))}")
            print(f"   - Hooks found: {result.get('hook_names', [])}")
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
            print(f"\n8️⃣  VALIDATING HOOKS:")
            print(f"   Checking if hooks exist in knowledge base...")
            is_valid, invalid_hooks = self.validator.validate_hooks(
                plugin_id, result["code"]
            )

            if not is_valid:
                print(f"   ❌ Hook validation FAILED")
                print(f"   Invalid hooks: {invalid_hooks}")
                return {
                    "action": "escalate",
                    "explanation": f"The solution requires hooks not available in {plugin_name}. Please contact our support team for custom development.",
                    "needs_escalation": True,
                    "reason": f"invalid_hooks: {', '.join(invalid_hooks)}",
                }

            print(f"   ✓ All hooks are valid")

            # Extract actual hooks used
            used_hooks = self.validator.extract_hooks_from_code(result["code"])
            result["hook_names"] = sorted(list(used_hooks))
            print(f"   Hooks extracted: {result['hook_names']}")

        print(f"\n9️⃣  FINAL RESPONSE:")
        print(f"   Action: {result.get('action')}")
        print(f"   Explanation: {result.get('explanation')[:80]}...")
        print(f"   Code length: {len(result.get('code', ''))} characters")
        print(f"   Hooks: {result.get('hook_names', [])}")
        print("\n" + "=" * 80 + "\n")

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
