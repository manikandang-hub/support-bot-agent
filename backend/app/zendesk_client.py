import requests
from typing import Optional


class ZendeskClient:
    """Client for Zendesk API ticket creation."""

    def __init__(self, zendesk_url: str, email: str, api_token: str):
        self.base_url = zendesk_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.auth = (f"{email}/token", api_token)

    def get_agent_id(self, agent_email: str) -> Optional[int]:
        """Resolve an agent email to their Zendesk user ID."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v2/users/search.json",
                params={"query": f"email:{agent_email}"},
                auth=self.auth,
                timeout=10,
            )
            if response.status_code == 200:
                users = response.json().get("users", [])
                if users:
                    return users[0]["id"]
        except Exception:
            pass
        return None

    def create_ticket(
        self,
        customer_email: str,
        plugin_name: str,
        query: str,
        analysis: str,
        title: str = None,
        attempted_solution: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ) -> dict:
        """
        Create a Zendesk support ticket with escalation context.

        Returns:
            dict with ticket_id, ticket_url, and created status
        """
        subject = title or f"[{plugin_name}] Support Request – {query[:60]}{'...' if len(query) > 60 else ''}"

        # Use provided description directly (pre-built from conversation), or build a default one
        if attempted_solution:
            description = attempted_solution
        else:
            description_parts = [
                "=" * 60,
                "SUPPORTBOT ESCALATION",
                "=" * 60,
                "",
                "CUSTOMER INFO",
                "-" * 30,
                f"Email:  {customer_email}",
                f"Plugin: {plugin_name}",
                "",
                "CUSTOMER QUERY",
                "-" * 30,
                query,
                "",
                "ANALYSIS",
                "-" * 30,
                analysis,
                "",
                "=" * 60,
                "This ticket was automatically created by SupportBot.",
            ]
            description = "\n".join(description_parts)

        ticket_payload = {
            "subject": subject,
            "description": description,
            "requester": {"email": customer_email},
            "tags": ["supportbot", plugin_name.lower().replace(" ", "-"), "escalation"],
            "priority": "normal",
            "type": "task",
        }

        if assignee_id:
            ticket_payload["assignee_id"] = assignee_id

        payload = {"ticket": ticket_payload}

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
                    "ticket_id": str(ticket_data["id"]),
                    "ticket_url": f"{self.base_url}/agent/tickets/{ticket_data['id']}",
                    "created": True,
                }
            else:
                return {
                    "ticket_id": None,
                    "ticket_url": None,
                    "created": False,
                    "error": f"Zendesk API error: {response.status_code} – {response.text}",
                }
        except Exception as e:
            return {
                "ticket_id": None,
                "ticket_url": None,
                "created": False,
                "error": str(e),
            }
