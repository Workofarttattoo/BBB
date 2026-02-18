"""
Tests for CollaborationHub feature.
"""
import pytest
import asyncio
from datetime import datetime
from blank_business_builder.all_features_implementation import CollaborationHub, Workspace

class TestCollaborationHub:

    def test_initialization(self):
        """Test that the hub initializes with no workspaces."""
        hub = CollaborationHub()
        assert hub.workspaces == {}

    def test_create_workspace(self):
        """Test creating a workspace."""
        hub = CollaborationHub()
        name = "Test Team"
        members = ["alice", "bob"]

        async def run_test():
            workspace = await hub.create_workspace(name, members)

            assert isinstance(workspace, Workspace)
            assert workspace.name == name
            assert workspace.members == members
            assert workspace.id in hub.workspaces
            assert hub.workspaces[workspace.id] == workspace
            assert isinstance(workspace.created_at, datetime)

        asyncio.run(run_test())

    def test_add_comment(self):
        """Test adding a comment to a workspace."""
        hub = CollaborationHub()

        async def run_test():
            # Create a workspace first
            workspace = await hub.create_workspace("Comment Team", ["charlie"])

            user = "charlie"
            text = "Hello world"

            comment = await hub.add_comment(workspace.id, user, text)

            assert comment["workspace_id"] == workspace.id
            assert comment["user"] == user
            assert comment["text"] == text
            assert "comment_id" in comment
            assert "timestamp" in comment

        asyncio.run(run_test())

    def test_multiple_workspaces(self):
        """Test managing multiple workspaces."""
        hub = CollaborationHub()

        async def run_test():
            w1 = await hub.create_workspace("Team A", ["user1"])
            w2 = await hub.create_workspace("Team B", ["user2"])

            assert len(hub.workspaces) == 2
            assert w1.id != w2.id
            assert hub.workspaces[w1.id].name == "Team A"
            assert hub.workspaces[w2.id].name == "Team B"

        asyncio.run(run_test())
