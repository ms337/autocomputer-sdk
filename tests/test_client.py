"""
Unit tests for the AutoComputer SDK client.
"""

import unittest
from unittest.mock import AsyncMock, Mock, patch

from autocomputer_sdk.client import AutoComputerClient


class TestAutoComputerClient(unittest.TestCase):
    """Test cases for the AutoComputerClient class."""

    def setUp(self):
        self.base_url = "https://test-api.autocomputer.ai"
        self.api_key = "test-api-key"
        self.client = AutoComputerClient(base_url=self.base_url, api_key=self.api_key)

    def test_client_initialization(self):
        self.assertEqual(self.client.base_url, self.base_url)
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(
            self.client.headers,
            {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
        )

    def test_namespaces_initialization(self):
        self.assertIsNotNone(self.client.workflows)
        self.assertIsNotNone(self.client.run)
        self.assertIsNotNone(self.client.computer)


class TestWorkflowsNamespace(unittest.IsolatedAsyncioTestCase):
    """Async tests for the WorkflowsNamespace class."""

    def setUp(self):
        self.client = AutoComputerClient(
            base_url="https://test-api.autocomputer.ai", api_key="test-api-key"
        )
        self.workflows = self.client.workflows

    @patch("httpx.AsyncClient.get")
    async def test_list_workflows(self, mock_get):
        # httpx.Response.json() and raise_for_status() are synchronous
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "workflows": [
                {
                    "workflow_id": "test-workflow-1",
                    "title": "Test Workflow 1",
                    "description": "This is a test workflow",
                },
                {
                    "workflow_id": "test-workflow-2",
                    "title": "Test Workflow 2",
                    "description": "This is another test workflow",
                },
            ]
        }
        mock_get.return_value = mock_response

        workflows = await self.workflows.list()

        self.assertEqual(len(workflows), 2)
        self.assertEqual(workflows[0].workflow_id, "test-workflow-1")
        self.assertEqual(workflows[0].title, "Test Workflow 1")
        self.assertEqual(workflows[1].workflow_id, "test-workflow-2")
        self.assertEqual(workflows[1].title, "Test Workflow 2")


# Additional tests would be added for other methods and namespaces
