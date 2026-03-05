"""Export worklog data to Azure Table Storage."""

from __future__ import annotations

import os
from typing import List

from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableServiceClient

from src.downloader import ProjectInfo, WorklogEntry


def _get_table_client():
    """Create and return an Azure Table Storage client.

    Reads connection settings from environment variables:
    - ``AZURE_STORAGE_CONNECTION_STRING``: full connection string (preferred), or
    - ``AZURE_STORAGE_ACCOUNT_NAME`` + ``AZURE_STORAGE_ACCOUNT_KEY``: account name and key.

    The table name is read from ``AZURE_TABLE_NAME`` (default: ``worklogs``).

    Raises
    ------
    KeyError
        If neither a connection string nor account name/key are set.
    """
    table_name = os.environ.get("AZURE_TABLE_NAME", "worklogs")

    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        service = TableServiceClient.from_connection_string(conn_str)
    else:
        account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
        account_key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
        endpoint = f"https://{account_name}.table.core.windows.net"
        service = TableServiceClient(
            endpoint=endpoint,
            credential={"account_name": account_name, "account_key": account_key},
        )

    try:
        service.create_table(table_name)
    except ResourceExistsError:
        pass

    return service.get_table_client(table_name)


def _worklog_to_entity(entry: WorklogEntry) -> dict:
    """Convert a :class:`~src.downloader.WorklogEntry` to an Azure Table entity.

    The entity uses ``project_key`` as the ``PartitionKey`` and
    ``worklog_id`` as the ``RowKey``.
    """
    return {
        "PartitionKey": entry.project_key,
        "RowKey": entry.worklog_id,
        "project_name": entry.project_name,
        "issue_key": entry.issue_key,
        "issue_summary": entry.issue_summary,
        "issue_type": entry.issue_type,
        "issue_status": entry.issue_status,
        "assignee": entry.assignee,
        "author": entry.author,
        "started": entry.started,
        "time_spent_seconds": entry.time_spent_seconds,
        "time_spent_hours": round(entry.time_spent_seconds / 3600, 2),
        "comment": entry.comment,
    }


def export_worklogs_to_azure(projects: List[ProjectInfo]) -> int:
    """Upsert all worklog entries into Azure Table Storage.

    Parameters
    ----------
    projects:
        List of :class:`~src.downloader.ProjectInfo` objects returned by
        :func:`~src.downloader.download`.

    Returns
    -------
    int
        Total number of worklog entries written.
    """
    table_client = _get_table_client()

    all_entries: List[WorklogEntry] = [wl for p in projects for wl in p.worklog_entries]

    for entry in all_entries:
        entity = _worklog_to_entity(entry)
        table_client.upsert_entity(entity)

    return len(all_entries)
