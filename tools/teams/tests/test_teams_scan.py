import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scan-teams-graph.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scan_teams_graph", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


scan_module = _load_module()


class TestTeamsReplies(unittest.TestCase):
    def test_contains_text_is_case_spacing_and_fuzzy_tolerant(self):
        scanner = scan_module.TeamsScanner.__new__(scan_module.TeamsScanner)
        self.assertTrue(scanner._contains_text("New Manager Assimilation", "newmanagerassimilation"))
        self.assertTrue(scanner._contains_text("General", "genral"))  # typo tolerance
        self.assertTrue(scanner._contains_text("ODA Team East", "oda teameast"))
        self.assertFalse(scanner._contains_text("Battery Operations", "invoice"))

    def test_list_channel_message_replies_endpoint(self):
        scanner = scan_module.TeamsScanner.__new__(scan_module.TeamsScanner)
        captured = {}

        def fake_paginated(endpoint, max_items=None):
            captured["endpoint"] = endpoint
            captured["max_items"] = max_items
            return []

        scanner._make_paginated_request = fake_paginated
        scanner.list_channel_message_replies("team-1", "channel-1", "message-1", limit=25)

        self.assertIn("/teams/team-1/channels/channel-1/messages/message-1/replies", captured["endpoint"])
        self.assertEqual(captured["max_items"], 25)

    def test_scan_teams_includes_message_replies_in_json(self):
        class FakeScanner(scan_module.TeamsScanner):
            def __init__(self):
                self.workspace_root = Path("/tmp")

            def list_teams_groups(self):
                return [{"id": "team-1", "displayName": "Alpha Team"}]

            def list_joined_teams(self):
                return [{"id": "team-1", "displayName": "Alpha Team", "description": "Demo"}]

            def list_team_channels(self, team_id):
                return [{"id": "channel-1", "displayName": "General", "membershipType": "standard", "webUrl": "https://example"}]

            def list_channel_messages(self, team_id, channel_id, limit=50):
                return [{
                    "id": "message-1",
                    "createdDateTime": "2026-01-01T00:00:00Z",
                    "lastModifiedDateTime": "2026-01-01T00:00:00Z",
                    "subject": "Subject",
                    "summary": "Summary",
                    "webUrl": "https://example/message-1",
                    "body": {"content": "<p>Hello team</p>"},
                    "from": {"user": {"displayName": "Alice"}}
                }]

            def list_channel_message_replies(self, team_id, channel_id, message_id, limit=50):
                return [{
                    "id": "reply-1",
                    "createdDateTime": "2026-01-01T00:01:00Z",
                    "lastModifiedDateTime": "2026-01-01T00:01:00Z",
                    "subject": None,
                    "summary": "Reply summary",
                    "webUrl": "https://example/reply-1",
                    "body": {"content": "<div>Roger that</div>"},
                    "from": {"user": {"displayName": "Bob"}},
                    "replyToId": "message-1"
                }]

        scanner = FakeScanner()
        results = scanner.scan_teams(include_messages=True, include_replies=True, message_limit=10, reply_limit=10)

        channel = results["teams"][0]["channels"][0]
        self.assertEqual(channel["messages_count"], 1)
        self.assertEqual(channel["replies_count"], 1)
        self.assertIn("messages", channel)
        self.assertEqual(channel["messages"][0]["replies_count"], 1)
        self.assertEqual(channel["messages"][0]["replies"][0]["id"], "reply-1")
        self.assertEqual(channel["messages"][0]["replies"][0]["from"], "Bob")

    def test_scan_teams_can_filter_team_channel_and_message_text(self):
        class FakeScanner(scan_module.TeamsScanner):
            def __init__(self):
                self.workspace_root = Path("/tmp")

            def list_teams_groups(self):
                return [{"id": "team-1", "displayName": "Alpha Team"}]

            def list_joined_teams(self):
                return [
                    {"id": "team-1", "displayName": "Alpha Team", "description": "Demo"},
                    {"id": "team-2", "displayName": "Beta Team", "description": "Demo"},
                ]

            def list_team_channels(self, team_id):
                if team_id == "team-1":
                    return [
                        {"id": "channel-1", "displayName": "General", "membershipType": "standard", "webUrl": "https://example"},
                        {"id": "channel-2", "displayName": "Ops", "membershipType": "standard", "webUrl": "https://example"},
                    ]
                return []

            def list_channel_messages(self, team_id, channel_id, limit=50):
                return [
                    {"id": "m1", "body": {"content": "<p>Hello world</p>"}},
                    {"id": "m2", "body": {"content": "<p>Target keyword appears here</p>"}},
                ]

            def list_channel_message_replies(self, team_id, channel_id, message_id, limit=50):
                return []

        scanner = FakeScanner()
        results = scanner.scan_teams(
            include_messages=True,
            include_replies=False,
            team_name="alpha",
            channel_name="general",
            message_contains="target keyword",
        )

        self.assertEqual(len(results["teams"]), 1)
        team = results["teams"][0]
        self.assertEqual(team["id"], "team-1")
        self.assertEqual(len(team["channels"]), 1)
        channel = team["channels"][0]
        self.assertEqual(channel["id"], "channel-1")
        self.assertEqual(channel["messages_count"], 1)
        self.assertEqual(channel["messages"][0]["id"], "m2")


if __name__ == "__main__":
    unittest.main()
