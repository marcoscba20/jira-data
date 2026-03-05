"""Unit tests for the azure_table_exporter module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.azure_table_exporter import _worklog_to_entity, export_worklogs_to_azure
from src.downloader import ProjectInfo, WorklogEntry


def _make_worklog_entry(**kwargs):
    defaults = dict(
        project_key="PROJ",
        project_name="Project One",
        issue_key="PROJ-1",
        issue_summary="Fix the bug",
        issue_type="Bug",
        issue_status="Done",
        assignee="Alice",
        worklog_id="1",
        author="Alice",
        started="2024-01-01T09:00:00.000+0000",
        time_spent_seconds=3600,
        comment="Done",
    )
    defaults.update(kwargs)
    return WorklogEntry(**defaults)


def _make_project(key="PROJ", name="Project One", lead="Bob", issue_count=5, worklogs=None):
    return ProjectInfo(
        key=key,
        name=name,
        lead=lead,
        issue_count=issue_count,
        worklog_entries=worklogs or [],
    )


class TestWorklogToEntity:
    def test_partition_key_is_project_key(self):
        entry = _make_worklog_entry(project_key="DEMO")
        entity = _worklog_to_entity(entry)
        assert entity["PartitionKey"] == "DEMO"

    def test_row_key_is_worklog_id(self):
        entry = _make_worklog_entry(worklog_id="42")
        entity = _worklog_to_entity(entry)
        assert entity["RowKey"] == "42"

    def test_time_spent_hours_conversion(self):
        entry = _make_worklog_entry(time_spent_seconds=7200)
        entity = _worklog_to_entity(entry)
        assert entity["time_spent_hours"] == 2.0

    def test_all_fields_present(self):
        entry = _make_worklog_entry()
        entity = _worklog_to_entity(entry)
        expected_fields = {
            "PartitionKey", "RowKey", "project_name", "issue_key", "issue_summary",
            "issue_type", "issue_status", "assignee", "author", "started",
            "time_spent_seconds", "time_spent_hours", "comment",
        }
        assert expected_fields == set(entity.keys())


class TestExportWorklogsToAzure:
    def _make_table_client_mock(self):
        table_client = MagicMock()
        return table_client

    @patch("src.azure_table_exporter._get_table_client")
    def test_returns_count_of_entries(self, mock_get_client):
        mock_get_client.return_value = self._make_table_client_mock()
        wl1 = _make_worklog_entry(worklog_id="1")
        wl2 = _make_worklog_entry(worklog_id="2")
        project = _make_project(worklogs=[wl1, wl2])

        count = export_worklogs_to_azure([project])

        assert count == 2

    @patch("src.azure_table_exporter._get_table_client")
    def test_upsert_called_for_each_entry(self, mock_get_client):
        table_client = self._make_table_client_mock()
        mock_get_client.return_value = table_client
        wl = _make_worklog_entry()
        project = _make_project(worklogs=[wl])

        export_worklogs_to_azure([project])

        assert table_client.upsert_entity.call_count == 1

    @patch("src.azure_table_exporter._get_table_client")
    def test_empty_projects_returns_zero(self, mock_get_client):
        mock_get_client.return_value = self._make_table_client_mock()

        count = export_worklogs_to_azure([])

        assert count == 0

    @patch("src.azure_table_exporter._get_table_client")
    def test_upsert_entity_receives_correct_keys(self, mock_get_client):
        table_client = self._make_table_client_mock()
        mock_get_client.return_value = table_client
        wl = _make_worklog_entry(project_key="PROJ", worklog_id="99")
        project = _make_project(worklogs=[wl])

        export_worklogs_to_azure([project])

        entity = table_client.upsert_entity.call_args[0][0]
        assert entity["PartitionKey"] == "PROJ"
        assert entity["RowKey"] == "99"

    @patch("src.azure_table_exporter._get_table_client")
    def test_multiple_projects(self, mock_get_client):
        table_client = self._make_table_client_mock()
        mock_get_client.return_value = table_client
        wl1 = _make_worklog_entry(project_key="P1", worklog_id="1")
        wl2 = _make_worklog_entry(project_key="P2", worklog_id="2")
        p1 = _make_project(key="P1", worklogs=[wl1])
        p2 = _make_project(key="P2", worklogs=[wl2])

        count = export_worklogs_to_azure([p1, p2])

        assert count == 2
        assert table_client.upsert_entity.call_count == 2
