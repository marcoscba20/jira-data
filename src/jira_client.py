"""Jira API client wrapper."""

import os

from dotenv import load_dotenv
from jira import JIRA

load_dotenv()


def create_jira_client() -> JIRA:
    """Create and return an authenticated Jira client using environment variables."""
    url = os.environ["JIRA_URL"]
    user = os.environ["JIRA_USER"]
    token = os.environ["JIRA_TOKEN"]
    return JIRA(server=url, basic_auth=(user, token))
