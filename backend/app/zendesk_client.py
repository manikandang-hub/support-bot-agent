import requests
import json
from typing import Optional


class ZendeskClient:
    """Client for Zendesk API ticket creation."""

    def __init__(self, zendesk_url: str, email: str, api_token: str):
        self.base_url = zendesk_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.auth = (f"{email}/token", api_token)

    def create_ticket(
        self,
        customer_email: str,
        plugin_name: str,
        query: str,
        analysis: str,
        attempted_solution: Optional[str] = None,
    ) -> dict:
        """
        Create a Zendesk support ticket with escalation context.

        Returns:
            dict with ticket_id, ticket_url, and created status
        """
        description = f"""SupportBot Escalation

Customer Query:
{query}

Analysis:
{analysis}
"""
        if attempted_solution:
            description += f"\nAttempted Solution:\n{attempted_solution}"

        description += f"\n\nPlugin: {plugin_name}\nCustomer Email: {customer_email}"

        payload = {
            "ticket": {
                "subject": f"[{plugin_name}] SupportBot Escalation - Plugin Change Needed",
                "description": description,
                "requester": {"email": customer_email},
                "tags": ["supportbot", plugin_name.lower().replace(" ", "-"), "escalation"],
                "priority": "normal",
                "type": "task",
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v2/tickets.json",
                json=payload,
                auth=self.auth,
                timeout=10,
            )

            if response.status_code == 201:
                ticket_data = response.json()["ticket"]
                return {
                    "ticket_id": ticket_data["id"],
                    "ticket_url": f"{self.base_url}/agent/tickets/{ticket_data['id']}",
                    "created": True,
                }
            else:
                return {
                    "ticket_id": None,
                    "ticket_url": None,
                    "created": False,
                    "error": f"Zendesk API error: {response.status_code}",
                }
        except Exception as e:
            return {
                "ticket_id": None,
                "ticket_url": None,
                "created": False,
                "error": str(e),
            }
