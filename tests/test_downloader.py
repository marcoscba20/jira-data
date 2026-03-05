"""Unit tests for the downloader module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.downloader import (
    ProjectInfo,
    WorklogEntry,
    _get_project_keys,
    _fetch_worklogs_for_project,
    download,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_issue(key="PROJ-1", summary="Test issue", issue_type="Task",
                status="To Do", assignee_name="Alice", project_key="PROJ",
                project_name="Project One"):
    issue = MagicMock()
    issue.id = "10001"
    issue.key = key
    issue.fields.summary = summary
    issue.fields.issuetype.name = issue_type
    issue.fields.status.name = status
    issue.fields.assignee.displayName = assignee_name
    issue.fields.project.name = project_name
    issue.fields.project.key = project_key
    return issue


def _make_worklog(wl_id="1", author="Alice", started="2024-01-01T09:00:00.000+0000",
                  seconds=3600, comment="Fixed it"):
    wl = MagicMock()
    wl.id = wl_id
    wl.author.displayName = author
    wl.started = started
    wl.timeSpentSeconds = seconds
    wl.comment = comment
    return wl


def _make_jira_client(projects=None, issues=None, worklogs=None):
    """Return a mocked JIRA client."""
    client = MagicMock()

    if projects is None:
        projects = [MagicMock(key="PROJ")]
    client.projects.return_value = projects

    if issues is None:
        issue = _make_issue()
        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([issue])
        issues_result.__bool__ = lambda self: True
        issues_result.total = 1
        issues = issues_result

    client.search_issues.return_value = issues

    if worklogs is None:
        worklogs = [_make_worklog()]
    client.worklogs.return_value = worklogs

    project_mock = MagicMock()
    project_mock.name = "Project One"
    project_mock.lead.displayName = "Bob"
    client.project.return_value = project_mock

    return client


# ---------------------------------------------------------------------------
# _get_project_keys
# ---------------------------------------------------------------------------

class TestGetProjectKeys:
    def test_returns_requested_keys_when_provided(self):
        client = MagicMock()
        assert _get_project_keys(client, ["PROJ", "DEMO"]) == ["PROJ", "DEMO"]

    def test_fetches_all_projects_when_none_requested(self):
        client = MagicMock()
        client.projects.return_value = [MagicMock(key="PROJ"), MagicMock(key="DEMO")]
        assert _get_project_keys(client) == ["PROJ", "DEMO"]

    def test_fetches_all_projects_when_empty_list(self):
        client = MagicMock()
        client.projects.return_value = [MagicMock(key="X")]
        assert _get_project_keys(client, []) == ["X"]


# ---------------------------------------------------------------------------
# _fetch_worklogs_for_project
# ---------------------------------------------------------------------------

class TestFetchWorklogsForProject:
    def test_returns_worklog_entries(self):
        wl = _make_worklog(seconds=7200)
        issue = _make_issue()

        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([issue])
        issues_result.__bool__ = lambda self: True
        issues_result.total = 1

        client = MagicMock()
        client.search_issues.return_value = issues_result
        client.worklogs.return_value = [wl]

        entries = _fetch_worklogs_for_project(client, "PROJ")

        assert len(entries) == 1
        entry = entries[0]
        assert entry.project_key == "PROJ"
        assert entry.issue_key == "PROJ-1"
        assert entry.time_spent_seconds == 7200
        assert entry.author == "Alice"

    def test_empty_worklogs(self):
        issue = _make_issue()

        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([issue])
        issues_result.__bool__ = lambda self: True
        issues_result.total = 1

        client = MagicMock()
        client.search_issues.return_value = issues_result
        client.worklogs.return_value = []

        entries = _fetch_worklogs_for_project(client, "PROJ")
        assert entries == []

    def test_no_issues(self):
        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([])
        issues_result.__bool__ = lambda self: False
        issues_result.total = 0

        client = MagicMock()
        client.search_issues.return_value = issues_result

        entries = _fetch_worklogs_for_project(client, "EMPTY")
        assert entries == []

    def test_issue_without_assignee(self):
        issue = _make_issue()
        issue.fields.assignee = None

        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([issue])
        issues_result.__bool__ = lambda self: True
        issues_result.total = 1

        client = MagicMock()
        client.search_issues.return_value = issues_result
        client.worklogs.return_value = [_make_worklog()]

        entries = _fetch_worklogs_for_project(client, "PROJ")
        assert entries[0].assignee == ""


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------

class TestDownload:
    def test_download_returns_project_info(self):
        client = _make_jira_client()
        # Make search_issues return proper total for issue_count query too
        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([_make_issue()])
        issues_result.__bool__ = lambda self: True
        issues_result.total = 1
        client.search_issues.return_value = issues_result

        results = download(client, project_keys=["PROJ"])

        assert len(results) == 1
        assert isinstance(results[0], ProjectInfo)
        assert results[0].key == "PROJ"
        assert results[0].name == "Project One"
        assert results[0].lead == "Bob"

    def test_download_populates_worklogs(self):
        client = _make_jira_client()
        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([_make_issue()])
        issues_result.__bool__ = lambda self: True
        issues_result.total = 1
        client.search_issues.return_value = issues_result
        client.worklogs.return_value = [_make_worklog()]

        results = download(client, project_keys=["PROJ"])

        assert len(results[0].worklog_entries) == 1
        assert isinstance(results[0].worklog_entries[0], WorklogEntry)

    def test_download_no_project_keys_uses_all(self):
        client = _make_jira_client()
        client.projects.return_value = [MagicMock(key="PROJ")]
        issues_result = MagicMock()
        issues_result.__iter__ = lambda self: iter([])
        issues_result.__bool__ = lambda self: False
        issues_result.total = 0
        client.search_issues.return_value = issues_result

        results = download(client)

        client.projects.assert_called_once()
        assert len(results) == 1
