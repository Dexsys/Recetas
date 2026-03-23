import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import create_app
from routes.auth import send_new_registration_email_to_admin


class RegistrationEmailTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()

    def test_builds_and_sends_admin_notification_email(self):
        fake_user = SimpleNamespace(id=123, username="Luis", email="luis@example.com")

        with self.app.test_request_context("/auth/register", base_url="http://127.0.0.1:5110"):
            with patch("routes.auth._send_email_message", return_value=True) as send_mock:
                sent = send_new_registration_email_to_admin(fake_user)

        self.assertTrue(sent)
        send_mock.assert_called_once()

        msg = send_mock.call_args[0][0]
        self.assertEqual(msg["To"], self.app.config.get("REGISTRATION_ALERT_EMAIL"))
        self.assertIn("Nuevo usuario pendiente de aprobacion", msg["Subject"])

        body = msg.get_content()
        self.assertIn("Aprobar:", body)
        self.assertIn("Rechazar y eliminar:", body)
        self.assertIn("Luis", body)
        self.assertIn("luis@example.com", body)


if __name__ == "__main__":
    unittest.main()
