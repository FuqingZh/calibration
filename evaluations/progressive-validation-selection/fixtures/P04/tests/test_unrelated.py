from unittest import TestCase


class NotificationTests(TestCase):
    def test_notification_label(self) -> None:
        self.assertEqual("notice".upper(), "NOTICE")
