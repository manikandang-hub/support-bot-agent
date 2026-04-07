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
        zendesk_agent_email: str = None,
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

        # Resolve agent email → Zendesk user ID at startup
        self.assignee_id = None
        if zendesk_agent_email:
            self.assignee_id = self.zendesk_client.get_agent_id(zendesk_agent_email)

    def process_query(
        self, plugin_id: str, query: str, customer_email: str, conversation_id: str = None
    ) -> dict:
        """
        Process a customer query and return either a code solution or a permission request.

        Returns:
            {
                "action": "snippet" | "ask_permission",
                "explanation": str,
                "code": str (if snippet),
                "hook_names": list (if snippet),
                "reason": str (if ask_permission),
                "conversation_id": str,
                "conversation_history": list,
            }
        """
        # Create or use existing conversation
        if not conversation_id:
            conversation_id = conversation_manager.create_conversation()

        # Add user message to conversation history
        conversation_manager.add_user_message(conversation_id, query)

        # Validate plugin exists
        if plugin_id not in PLUGIN_METADATA:
            reason = f"Plugin '{plugin_id}' not found. Please select a valid plugin."
            conversation_manager.add_assistant_message(conversation_id, explanation=reason)
            conversation_manager.store_pending_escalation(conversation_id, {
                "plugin_name": plugin_id,
                "query": query,
                "analysis": reason,
            })
            return {
                "action": "ask_permission",
                "explanation": reason,
                "reason": reason,
                "conversation_id": conversation_id,
                "conversation_history": conversation_manager.get_conversation_history(conversation_id),
            }

        plugin_info = PLUGIN_METADATA[plugin_id]
        plugin_name = plugin_info["name"]

        # Get available hooks for this plugin
        available_hooks = self.validator.get_available_hooks(plugin_id)

        if not available_hooks:
            reason = f"No knowledge base available for {plugin_name}. I'll need to escalate this to our support team."
            conversation_manager.add_assistant_message(conversation_id, explanation=reason)
            conversation_manager.store_pending_escalation(conversation_id, {
                "plugin_name": plugin_name,
                "query": query,
                "analysis": reason,
            })
            return {
                "action": "ask_permission",
                "explanation": reason,
                "reason": reason,
                "conversation_id": conversation_id,
                "conversation_history": conversation_manager.get_conversation_history(conversation_id),
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

        # If LLM determined escalation is needed, ask permission first
        if solution.get("action") == "escalate":
            analysis = solution.get("explanation", "")
            conversation_manager.store_pending_escalation(conversation_id, {
                "plugin_name": plugin_name,
                "query": query,
                "analysis": analysis,
            })
            return {
                "action": "ask_permission",
                "explanation": analysis,
                "reason": solution.get("reason", analysis),
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

    def prepare_ticket(
        self, conversation_id: str, customer_email: str, plugin_id: str
    ) -> dict:
        """
        Build a suggested ticket title and description from the conversation history.
        Returns title and description for the user to review/edit before submission.
        """
        pending = conversation_manager.get_pending_escalation(conversation_id)
        # Re-store so it's still available when confirm is called
        if pending:
            conversation_manager.store_pending_escalation(conversation_id, pending)

        history = conversation_manager.get_conversation_history(conversation_id)
        plugin_name = (pending or {}).get("plugin_name") or \
                      PLUGIN_METADATA.get(plugin_id, {}).get("name", plugin_id)

        # Use LLM to generate a clean, summarised title and description
        summary = self.code_generator.generate_ticket_summary(
            plugin_name=plugin_name,
            customer_email=customer_email,
            conversation_history=history,
        )
        return summary

    def confirm_ticket_creation(
        self, conversation_id: str, customer_email: str, plugin_id: str,
        title: str = None, description: str = None
    ) -> dict:
        """
        Create a Zendesk ticket after user has given permission.
        Retrieves stored escalation context and creates the ticket.
        """
        pending = conversation_manager.get_pending_escalation(conversation_id)

        if not pending:
            return {
                "action": "escalate",
                "explanation": "No pending escalation found. Please try your question again.",
                "ticket_id": None,
                "ticket_url": None,
                "reason": "Session expired",
                "conversation_id": conversation_id,
                "conversation_history": conversation_manager.get_conversation_history(conversation_id),
            }

        plugin_name = pending.get("plugin_name", PLUGIN_METADATA.get(plugin_id, {}).get("name", plugin_id))
        query = pending.get("query", "")
        analysis = pending.get("analysis", "")

        # Use user-provided title/description or fall back to auto-generated
        if not title:
            short_query = query[:70] + ("..." if len(query) > 70 else "")
            title = f"[{plugin_name}] Support Request – {short_query}"

        ticket_result = self.zendesk_client.create_ticket(
            customer_email=customer_email,
            plugin_name=plugin_name,
            query=query,
            analysis=analysis,
            title=title,
            attempted_solution=description,  # pass user-edited description as context
            assignee_id=self.assignee_id,
        )

        return {
            "action": "escalate",
            "explanation": "A support ticket has been created and assigned to our team. We'll get back to you within 24 hours.",
            "ticket_id": ticket_result.get("ticket_id"),
            "ticket_url": ticket_result.get("ticket_url"),
            "reason": analysis,
            "conversation_id": conversation_id,
            "conversation_history": conversation_manager.get_conversation_history(conversation_id),
        }
