from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

PAGE_SIZE = 500
GITHUB_PAGE_SIZE = 100


def request_json(url: str, token: str, *, github: bool = False, method: str = "GET", payload=None):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    if github:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            if response.status == 204:
                return None
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API request failed ({error.code}) at {request.full_url.split('?')[0]}: {details}") from error


def project_key_from_config() -> str:
    config_path = Path(__file__).resolve().parents[1] / "sonar-project.properties"
    for line in config_path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "sonar.projectKey":
            return value.strip()
    raise RuntimeError(f"sonar.projectKey is missing from {config_path}")


def fetch_findings(sonar_url: str, sonar_token: str, project_key: str) -> list[dict]:
    findings = []
    page = 1
    while True:
        query = urlencode({
            "componentKeys": project_key,
            "resolved": "false",
            "ps": PAGE_SIZE,
            "p": page,
        })
        response = request_json(
            f"{sonar_url}/api/issues/search?{query}",
            sonar_token,
        )
        page_findings = response.get("issues", [])
        findings.extend(page_findings)
        paging = response.get("paging", {})
        total = paging.get("total", len(findings))
        if not page_findings or len(findings) >= total:
            return findings
        page += 1


def fetch_existing_issues(github_api: str, token: str, repository: str) -> dict[str, dict]:
    existing = {}
    page = 1
    repository_path = quote(repository, safe="/")
    while True:
        query = urlencode({"state": "all", "per_page": GITHUB_PAGE_SIZE, "page": page})
        issues = request_json(
            f"{github_api}/repos/{repository_path}/issues?{query}",
            token,
            github=True,
        )
        for issue in issues:
            if "pull_request" in issue:
                continue
            body = issue.get("body") or ""
            start = body.find("<!-- sonar-issue-key:")
            if start == -1:
                continue
            key_start = start + len("<!-- sonar-issue-key:")
            key_end = body.find(" -->", key_start)
            if key_end != -1:
                existing[body[key_start:key_end]] = issue
        if len(issues) < GITHUB_PAGE_SIZE:
            return existing
        page += 1


def issue_content(finding: dict, project_key: str, sonar_url: str) -> tuple[str, str]:
    issue_key = finding["key"]
    severity = finding.get("severity", "UNKNOWN")
    message = finding.get("message", "SonarQube finding")
    title = f"[SonarQube] {severity}: {message}"[:250]
    component = finding.get("component", "")
    if component.startswith(f"{project_key}:"):
        component = component[len(project_key) + 1:]
    issue_url = f"{sonar_url}/project/issues?{urlencode({'id': project_key, 'open': issue_key})}"
    line = finding.get("line")
    body = "\n".join([
        f"<!-- sonar-issue-key:{issue_key} -->",
        "Automated report from the SonarQube scan.",
        "",
        f"- **Severity:** {html.escape(str(severity))}",
        f"- **Type:** {html.escape(str(finding.get('type', 'Unknown')))}",
        f"- **Rule:** `{html.escape(str(finding.get('rule', 'Unknown')))}`",
        f"- **File:** `{html.escape(component or 'Unknown')}`",
        f"- **Line:** {line if line is not None else 'Not specified'}",
        f"- **SonarQube:** {issue_url}",
        "",
        "**Finding**",
        "",
        f"<pre>{html.escape(str(message))}</pre>",
    ])
    return title, body


def sync_findings() -> tuple[int, int, int]:
    sonar_url = os.environ["SONAR_HOST_URL"].rstrip("/")
    sonar_token = os.environ["SONAR_TOKEN"]
    github_token = os.environ["GH_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]
    github_api = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    project_key = project_key_from_config()

    findings = fetch_findings(sonar_url, sonar_token, project_key)
    existing = fetch_existing_issues(github_api, github_token, repository)
    repository_path = quote(repository, safe="/")
    created = updated = unchanged = 0

    for finding in findings:
        issue_key = finding["key"]
        title, body = issue_content(finding, project_key, sonar_url)
        tracked = existing.get(issue_key)
        if tracked is None:
            request_json(
                f"{github_api}/repos/{repository_path}/issues",
                github_token,
                github=True,
                method="POST",
                payload={"title": title, "body": body},
            )
            created += 1
            continue

        updates = {}
        if tracked.get("title") != title:
            updates["title"] = title
        if tracked.get("body") != body:
            updates["body"] = body
        if tracked.get("state") != "open":
            updates["state"] = "open"
        if updates:
            request_json(
                f"{github_api}/repos/{repository_path}/issues/{tracked['number']}",
                github_token,
                github=True,
                method="PATCH",
                payload=updates,
            )
            updated += 1
        else:
            unchanged += 1

    print(
        f"SonarQube findings: {len(findings)} unresolved; "
        f"GitHub issues created={created}, updated/reopened={updated}, unchanged={unchanged}."
    )
    return created, updated, unchanged


if __name__ == "__main__":
    sync_findings()