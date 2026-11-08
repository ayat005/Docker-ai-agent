
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class ChatViewTests(TestCase):

    def test_chat_page_loads(self):
        response = self.client.get(reverse("chat"))

        self.assertEqual(response.status_code, 200)

    @patch("chat.views.run_agent")
    def test_send_message(self, mock_run_agent):
        mock_run_agent.return_value = ("Hello! How can I help?", "test-interaction-123")

        response = self.client.post(
            reverse("chat"),
            {"message": "Show me the inventory"},
        )

        self.assertEqual(response.status_code, 302)
        mock_run_agent.assert_called_once_with("Show me the inventory", None)

        session = self.client.session
        self.assertEqual(
            session["history"],
            [
                {"role": "user", "text": "Show me the inventory"},
                {"role": "agent", "text": "Hello! How can I help?"},
            ],
        )
        self.assertEqual(
            session["interaction_id"],
            "test-interaction-123",
        )

    @patch("chat.views.run_agent")
    def test_empty_message_does_not_call_agent(self, mock_run_agent):
        response = self.client.post(
            reverse("chat"),
            {"message": "   "},
        )

        self.assertEqual(response.status_code, 302)
        mock_run_agent.assert_not_called()

    def test_reset_clears_session(self):
        session = self.client.session
        session["history"] = [{"role": "user", "text": "Hello"}]
        session["interaction_id"] = "test-interaction-123"
        session.save()

        response = self.client.get(reverse("reset"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("history"), None)
        self.assertEqual(self.client.session.get("interaction_id"), None)

    @patch("chat.views.run_agent")
    def test_agent_error_is_handled(self, mock_run_agent):
        mock_run_agent.side_effect = Exception("Test API error")

        response = self.client.post(
            reverse("chat"),
            {"message": "Show me the inventory"},
        )

        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertEqual(
            session["history"][-1]["text"],
            "Something went wrong: Test API error",
        )
