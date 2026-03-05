"""Export downloaded Jira data to CSV files."""

from __future__ import annotations

import csv
import os
from typing import List

from src.downloader import ProjectInfo, WorklogEntry


def _ensure_dir(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)


def export_worklogs(projects: List[ProjectInfo], output_dir: str = "output") -> str:
    """Write all worklog entries to a CSV file.

    Parameters
    ----------
    projects:
        List of :class:`~src.downloader.ProjectInfo` objects returned by
        :func:`~src.downloader.download`.
    output_dir:
        Directory where the CSV file will be created.

    Returns
    -------
    str
        Path to the created file.
    """
    _ensure_dir(output_dir)
    path = os.path.join(output_dir, "worklogs.csv")

    fieldnames = [
        "project_key",
        "project_name",
        "issue_key",
        "issue_summary",
        "issue_type",
        "issue_status",
        "assignee",
        "worklog_id",
        "author",
        "started",
        "time_spent_seconds",
        "time_spent_hours",
        "comment",
    ]

    all_entries: List[WorklogEntry] = [wl for p in projects for wl in p.worklog_entries]

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for entry in all_entries:
            writer.writerow(
                {
                    "project_key": entry.project_key,
                    "project_name": entry.project_name,
                    "issue_key": entry.issue_key,
                    "issue_summary": entry.issue_summary,
                    "issue_type": entry.issue_type,
                    "issue_status": entry.issue_status,
                    "assignee": entry.assignee,
                    "worklog_id": entry.worklog_id,
                    "author": entry.author,
                    "started": entry.started,
                    "time_spent_seconds": entry.time_spent_seconds,
                    "time_spent_hours": round(entry.time_spent_seconds / 3600, 2),
                    "comment": entry.comment,
                }
            )

    return path


def export_projects(projects: List[ProjectInfo], output_dir: str = "output") -> str:
    """Write project summary data to a CSV file.

    Parameters
    ----------
    projects:
        List of :class:`~src.downloader.ProjectInfo` objects.
    output_dir:
        Directory where the CSV file will be created.

    Returns
    -------
    str
        Path to the created file.
    """
    _ensure_dir(output_dir)
    path = os.path.join(output_dir, "projects.csv")

    fieldnames = ["project_key", "project_name", "lead", "issue_count", "total_worklog_entries"]

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for project in projects:
            writer.writerow(
                {
                    "project_key": project.key,
                    "project_name": project.name,
                    "lead": project.lead,
                    "issue_count": project.issue_count,
                    "total_worklog_entries": len(project.worklog_entries),
                }
            )

    return path
