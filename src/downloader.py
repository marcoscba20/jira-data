"""Download worklogs and project data from Jira."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from jira import JIRA


@dataclass
class WorklogEntry:
    """Represents a single worklog record."""

    project_key: str
    project_name: str
    issue_key: str
    issue_summary: str
    issue_type: str
    issue_status: str
    assignee: str
    worklog_id: str
    author: str
    started: str
    time_spent_seconds: int
    comment: str


@dataclass
class ProjectInfo:
    """Represents basic project metadata."""

    key: str
    name: str
    lead: str
    issue_count: int
    worklog_entries: List[WorklogEntry] = field(default_factory=list)


def _get_project_keys(client: JIRA, requested: Optional[List[str]] = None) -> List[str]:
    """Return the list of project keys to process.

    If *requested* is provided and non-empty only those projects are used;
    otherwise all accessible projects are returned.
    """
    if requested:
        return requested
    return [p.key for p in client.projects()]


def _fetch_worklogs_for_project(client: JIRA, project_key: str) -> List[WorklogEntry]:
    """Fetch all worklog entries for every issue in *project_key*."""
    entries: List[WorklogEntry] = []

    start = 0
    page_size = 100
    while True:
        issues = client.search_issues(
            f"project = {project_key}",
            startAt=start,
            maxResults=page_size,
            fields="summary,issuetype,status,assignee,worklog",
            expand="",
        )
        if not issues:
            break

        for issue in issues:
            fields = issue.fields
            assignee = fields.assignee.displayName if fields.assignee else ""
            project_name = issue.fields.project.name

            # The worklogs may be paginated; fetch them all via the dedicated endpoint
            worklogs = client.worklogs(issue.id)
            for wl in worklogs:
                entries.append(
                    WorklogEntry(
                        project_key=project_key,
                        project_name=project_name,
                        issue_key=issue.key,
                        issue_summary=fields.summary,
                        issue_type=fields.issuetype.name,
                        issue_status=fields.status.name,
                        assignee=assignee,
                        worklog_id=wl.id,
                        author=wl.author.displayName,
                        started=wl.started,
                        time_spent_seconds=wl.timeSpentSeconds,
                        comment=getattr(wl, "comment", "") or "",
                    )
                )

        if start + page_size >= issues.total:
            break
        start += page_size

    return entries


def download(
    client: JIRA,
    project_keys: Optional[List[str]] = None,
) -> List[ProjectInfo]:
    """Download project data and worklogs from Jira.

    Parameters
    ----------
    client:
        Authenticated :class:`jira.JIRA` instance.
    project_keys:
        Optional list of project keys to restrict the download. When *None* or
        empty all accessible projects are downloaded.

    Returns
    -------
    List[ProjectInfo]
        One entry per project with its worklog entries populated.
    """
    keys = _get_project_keys(client, project_keys)
    results: List[ProjectInfo] = []

    for key in keys:
        project = client.project(key)
        lead = project.lead.displayName if project.lead else ""

        issue_count_result = client.search_issues(
            f"project = {key}",
            maxResults=0,
            fields="",
        )
        issue_count = issue_count_result.total

        worklogs = _fetch_worklogs_for_project(client, key)

        results.append(
            ProjectInfo(
                key=key,
                name=project.name,
                lead=lead,
                issue_count=issue_count,
                worklog_entries=worklogs,
            )
        )

    return results
