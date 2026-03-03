#!/usr/bin/env python3
"""Entry point for the Jira data downloader."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from src.downloader import download
from src.exporter import export_projects, export_worklogs
from src.jira_client import create_jira_client

load_dotenv()


def main() -> None:
    projects_env = os.environ.get("JIRA_PROJECTS", "").strip()
    project_keys = [k.strip() for k in projects_env.split(",") if k.strip()] or None

    output_dir = os.environ.get("OUTPUT_DIR", "output")

    print("Connecting to Jira...")
    client = create_jira_client()

    print("Downloading data...")
    projects = download(client, project_keys=project_keys)

    worklogs_path = export_worklogs(projects, output_dir=output_dir)
    projects_path = export_projects(projects, output_dir=output_dir)

    total_worklogs = sum(len(p.worklog_entries) for p in projects)
    print(f"Done. {len(projects)} project(s), {total_worklogs} worklog entry/entries exported.")
    print(f"  Worklogs -> {worklogs_path}")
    print(f"  Projects -> {projects_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyError as exc:
        print(f"Error: missing environment variable {exc}. See .env.example for reference.")
        sys.exit(1)
