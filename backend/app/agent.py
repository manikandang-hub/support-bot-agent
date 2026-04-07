from app.code_generator import CodeGenerator
from app.zendesk_client import ZendeskClient
from app.hooks_validator import HooksValidator
from app.conversation_manager import conversation_manager


PLUGIN_METADATA = {
    "product-feed": {
        "name": "WebToffee Product Feed Sync Manager Pro",
        "description": "Sync WooCommerce products to multiple channels",
    },
    "invoice-plugin": {
        "name": "WebToffee Invoice, Packing Slip & Credit Note",
        "description": "Generate invoices and packing slips for WooCommerce orders",
    },
}


class SupportAgent:
    """Main support agent that coordinates code generation and escalation."""

    def __init__(
        self,
        anthropic_api_key: str = None,
        openai_api_key: str = None,
        zendesk_url: str = None,
        zendesk_email: str = None,
        zendesk_api_token: str = None,
        knowledge_base_dir: str = "knowledge_base",
        llm_provider: str = "auto",
    ):
        self.code_generator = CodeGenerator(
            anthropic_key=anthropic_api_key,
            openai_key=openai_api_key,
            knowledge_base_dir=knowledge_base_dir,
            provider=llm_provider
        )
        self.zendesk_client = ZendeskClient(zendesk_url, zendesk_email, zendesk_api_token)
        self.validator = HooksValidator(knowledge_base_dir)

    def process_query(
        self, plugin_id: str, query: str, customer_email: str, conversation_id: str = None
    ) -> dict:
        """
        Process a customer query and return either a code solution or escalation.

        Args:
            plugin_id: Plugin identifier
            query: Customer's question
            customer_email: Customer email address
            conversation_id: Conversation ID for tracking multi-turn conversations

        Returns:
            {
                "action": "snippet" | "escalate",
                "explanation": str,
                "code": str (if snippet),
                "hook_names": list (if snippet),
                "ticket_id": str (if escalate),
                "ticket_url": str (if escalate),
                "conversation_id": str (new or existing),
                "conversation_history": list (previous messages),
            }
        """
        # Create or use existing conversation
        if not conversation_id:
            conversation_id = conversation_manager.create_conversation()

        # Add user message to conversation history
        conversation_manager.add_user_message(conversation_id, query)
        # Validate plugin exists
        if plugin_id not in PLUGIN_METADATA:
            return {
                "action": "escalate",
                "explanation": f"Plugin '{plugin_id}' not found. Please select a valid plugin.",
                "ticket_id": None,
                "ticket_url": None,
            }

        plugin_info = PLUGIN_METADATA[plugin_id]
        plugin_name = plugin_info["name"]

        # Get available hooks for this plugin
        available_hooks = self.validator.get_available_hooks(plugin_id)

        if not available_hooks:
            return {
                "action": "escalate",
                "explanation": f"No knowledge base available for {plugin_name}. Please contact support directly.",
                "ticket_id": None,
                "ticket_url": None,
                "conversation_id": conversation_id,
            }

        # Get conversation context for follow-up questions
        conversation_context = conversation_manager.get_context_for_followup(conversation_id)

        # Generate solution using Claude/OpenAI with conversation context
        solution = self.code_generator.generate_solution(
            plugin_id=plugin_id,
            plugin_name=plugin_name,
            query=query,
            available_hooks=available_hooks,
            conversation_context=conversation_context,
        )

        # Store assistant response in conversation history
        if solution.get("action") == "snippet":
            conversation_manager.add_assistant_message(
                conversation_id,
                explanation=solution.get("explanation", ""),
                code=solution.get("code"),
                hook_names=solution.get("hook_names", [])
            )
        else:
            conversation_manager.add_assistant_message(
                conversation_id,
                explanation=solution.get("explanation", ""),
            )

        # If solution is escalation, create Zendesk ticket
        if solution.get("action") == "escalate":
            ticket_result = self.zendesk_client.create_ticket(
                customer_email=customer_email,
                plugin_name=plugin_name,
                query=query,
                analysis=solution.get("explanation", ""),
                attempted_solution=None,
            )

            return {
                "action": "escalate",
                "explanation": solution.get("explanation", ""),
                "ticket_id": ticket_result.get("ticket_id"),
                "ticket_url": ticket_result.get("ticket_url"),
                "reason": solution.get("reason"),
                "conversation_id": conversation_id,
                "conversation_history": conversation_manager.get_conversation_history(conversation_id),
            }

        # Return code snippet with conversation history
        return {
            "action": "snippet",
            "explanation": solution.get("explanation", ""),
            "code": solution.get("code", ""),
            "hook_names": solution.get("hook_names", []),
            "conversation_id": conversation_id,
            "conversation_history": conversation_manager.get_conversation_history(conversation_id),
        }
