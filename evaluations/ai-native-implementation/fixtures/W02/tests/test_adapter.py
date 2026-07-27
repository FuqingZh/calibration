from unittest import TestCase

from src.adapter import accept_record


class AdapterTests(TestCase):
    def test_note_is_optional(self) -> None:
        record = {"name": "sample"}
        self.assertIs(accept_record(record), record)
