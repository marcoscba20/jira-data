"""Unit tests for the exporter module."""

from __future__ import annotations

import csv
import os

import pytest

from src.downloader import ProjectInfo, WorklogEntry
from src.exporter import export_projects, export_worklogs


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


class TestExportWorklogs:
    def test_creates_csv_file(self, tmp_path):
        wl = _make_worklog_entry(time_spent_seconds=3600)
        project = _make_project(worklogs=[wl])
        path = export_worklogs([project], output_dir=str(tmp_path))
        assert os.path.exists(path)

    def test_csv_has_correct_headers(self, tmp_path):
        project = _make_project()
        path = export_worklogs([project], output_dir=str(tmp_path))
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            assert "time_spent_hours" in reader.fieldnames
            assert "time_spent_seconds" in reader.fieldnames
            assert "project_key" in reader.fieldnames

    def test_time_spent_hours_conversion(self, tmp_path):
        wl = _make_worklog_entry(time_spent_seconds=7200)
        project = _make_project(worklogs=[wl])
        path = export_worklogs([project], output_dir=str(tmp_path))
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert float(rows[0]["time_spent_hours"]) == 2.0

    def test_empty_projects(self, tmp_path):
        path = export_worklogs([], output_dir=str(tmp_path))
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows == []

    def test_multiple_projects(self, tmp_path):
        wl1 = _make_worklog_entry(project_key="P1", issue_key="P1-1")
        wl2 = _make_worklog_entry(project_key="P2", issue_key="P2-1")
        p1 = _make_project(key="P1", worklogs=[wl1])
        p2 = _make_project(key="P2", worklogs=[wl2])
        path = export_worklogs([p1, p2], output_dir=str(tmp_path))
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2


class TestExportProjects:
    def test_creates_csv_file(self, tmp_path):
        project = _make_project()
        path = export_projects([project], output_dir=str(tmp_path))
        assert os.path.exists(path)

    def test_csv_contains_project_data(self, tmp_path):
        project = _make_project(key="DEMO", name="Demo Project", lead="Carol", issue_count=10)
        path = export_projects([project], output_dir=str(tmp_path))
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 1
        assert rows[0]["project_key"] == "DEMO"
        assert rows[0]["project_name"] == "Demo Project"
        assert rows[0]["lead"] == "Carol"
        assert int(rows[0]["issue_count"]) == 10

    def test_total_worklog_entries_count(self, tmp_path):
        wl1 = _make_worklog_entry()
        wl2 = _make_worklog_entry()
        project = _make_project(worklogs=[wl1, wl2])
        path = export_projects([project], output_dir=str(tmp_path))
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert int(rows[0]["total_worklog_entries"]) == 2

    def test_empty_projects(self, tmp_path):
        path = export_projects([], output_dir=str(tmp_path))
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows == []
