from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from html.parser import HTMLParser
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

PAGE_SIZE = 500
GITHUB_PAGE_SIZE = 100
SEVERITY_COLORS = {
    "blocker": "b60205",
    "critical": "d93f0b",
    "major": "fbca04",
    "minor": "0e8a16",
    "info": "1d76db",
}
TYPE_COLORS = {
    "bug": "d93f0b",
    "vulnerability": "b60205",
    "code-smell": "1d76db",
    "security-hotspot": "fbca04",
}


class PlainTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"br", "p", "li", "div", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


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


def normalized_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"


def finding_labels(finding: dict) -> list[tuple[str, str, str]]:
    severity = normalized_label(str(finding.get("severity", "unknown")))
    issue_type = normalized_label(str(finding.get("type", "unknown")))
    return [
        (
            f"sonar-severity/{severity}",
            SEVERITY_COLORS.get(severity, "ededed"),
            f"SonarQube severity: {severity.upper()}",
        ),
        (
            f"sonar-type/{issue_type}",
            TYPE_COLORS.get(issue_type, "ededed"),
            f"SonarQube issue type: {issue_type.upper()}",
        ),
    ]


def ensure_repository_labels(
    github_api: str,
    token: str,
    repository_path: str,
    label_specs: list[tuple[str, str, str]],
) -> None:
    existing = set()
    page = 1
    while True:
        query = urlencode({"per_page": GITHUB_PAGE_SIZE, "page": page})
        labels = request_json(
            f"{github_api}/repos/{repository_path}/labels?{query}",
            token,
            github=True,
        )
        existing.update(label["name"] for label in labels)
        if len(labels) < GITHUB_PAGE_SIZE:
            break
        page += 1

    for name, color, description in label_specs:
        if name in existing:
            continue
        request_json(
            f"{github_api}/repos/{repository_path}/labels",
            token,
            github=True,
            method="POST",
            payload={"name": name, "color": color, "description": description[:100]},
        )
        existing.add(name)


def sync_issue_labels(
    github_api: str,
    token: str,
    repository_path: str,
    issue: dict,
    labels: list[tuple[str, str, str]],
) -> bool:
    issue_url = f"{github_api}/repos/{repository_path}/issues/{issue['number']}/labels"
    expected = {name for name, _, _ in labels}
    current = {label["name"] for label in issue.get("labels", [])}
    managed_prefixes = ("sonar-severity/", "sonar-type/")
    changed = False

    for stale_label in current:
        if stale_label.startswith(managed_prefixes) and stale_label not in expected:
            request_json(
                f"{issue_url}/{quote(stale_label, safe='')}",
                token,
                github=True,
                method="DELETE",
            )
            changed = True

    missing = expected - current
    if missing:
        request_json(
            issue_url,
            token,
            github=True,
            method="POST",
            payload={"labels": sorted(missing)},
        )
        changed = True
    return changed


def rule_details(sonar_url: str, sonar_token: str, rule_key: str) -> dict:
    query = urlencode({"key": rule_key})
    response = request_json(f"{sonar_url}/api/rules/show?{query}", sonar_token)
    return response.get("rule", {})


def component_path(component: str, project_key: str) -> str:
    prefix = f"{project_key}:"
    return component[len(prefix):] if component.startswith(prefix) else component


def source_excerpt(component: str, project_key: str, finding: dict) -> str:
    repository_root = Path(__file__).resolve().parents[1]
    relative_path = Path(component_path(component, project_key))
    source_path = (repository_root / relative_path).resolve()
    if not source_path.is_relative_to(repository_root) or not source_path.is_file():
        return "Source excerpt is unavailable in the checked-out revision."

    try:
        lines = source_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return "Source excerpt is unavailable in the checked-out revision."

    text_range = finding.get("textRange") or {}
    start_line = text_range.get("startLine", finding.get("line"))
    end_line = text_range.get("endLine", start_line)
    if not isinstance(start_line, int) or not lines:
        return "SonarQube did not provide a source line for this finding."

    start_line = max(1, min(start_line, len(lines)))
    end_line = max(start_line, min(end_line if isinstance(end_line, int) else start_line, len(lines)))
    first_line = max(1, start_line - 4)
    last_line = min(len(lines), max(end_line + 4, start_line + 8))
    excerpt = [
        f"{line_number:>5}{' >' if start_line <= line_number <= end_line else '  '} {lines[line_number - 1]}"
        for line_number in range(first_line, last_line + 1)
    ]
    fence = "````"
    while fence in "\n".join(excerpt):
        fence += "`"
    return f"```text\n{chr(10).join(excerpt)}\n{fence}"


def flow_details(finding: dict, project_key: str) -> str:
    flows = finding.get("flows") or []
    sections = []
    for flow_index, flow in enumerate(flows, start=1):
        locations = []
        for location in flow.get("locations", []):
            component = component_path(location.get("component", ""), project_key)
            text_range = location.get("textRange") or {}
            line = text_range.get("startLine", "line not provided")
            message = location.get("msg", "")
            locations.append(f"- `{component}:{line}`: {message}")
        if locations:
            sections.append(f"**Flow {flow_index}**\n" + "\n".join(locations))
    return "\n\n".join(sections)


def issue_content(
    finding: dict,
    project_key: str,
    sonar_url: str,
    rule: dict | None = None,
    repository: str = "",
    commit_sha: str = "",
) -> tuple[str, str]:
    issue_key = finding["key"]
    severity = finding.get("severity", "UNKNOWN")
    message = finding.get("message", "SonarQube finding")
    title_prefix = f"{severity}: "
    title = f"{title_prefix}{message[:250 - len(title_prefix)]}"
    component = component_path(finding.get("component", ""), project_key)
    issue_url = f"{sonar_url}/project/issues?{urlencode({'id': project_key, 'open': issue_key})}"
    text_range = finding.get("textRange") or {}
    start_line = text_range.get("startLine", finding.get("line"))
    end_line = text_range.get("endLine", start_line)
    line_display = str(start_line) if start_line is not None else "Not specified"
    if end_line is not None and end_line != start_line:
        line_display = f"{line_display}-{end_line}"
    source_url = ""
    if repository and commit_sha and component:
        source_url = f"https://github.com/{repository}/blob/{commit_sha}/{quote(component, safe='/')}#L{start_line or 1}"

    rule = rule or {}
    rule_description = rule.get("mdDesc", "")
    if not rule_description and rule.get("htmlDesc"):
        extractor = PlainTextExtractor()
        extractor.feed(rule["htmlDesc"])
        rule_description = extractor.text()

    tags = finding.get("tags") or rule.get("tags") or []
    impacts = finding.get("impacts") or rule.get("impacts") or []
    impact_display = ", ".join(
        f"{impact.get('softwareQuality', 'quality')}: {impact.get('severity', 'unspecified')}"
        for impact in impacts
    )
    metadata = [
        f"- **Severity:** {html.escape(str(severity))}",
        f"- **Type:** {html.escape(str(finding.get('type', 'Unknown')))}",
        f"- **Rule:** `{html.escape(str(finding.get('rule', 'Unknown')))}`",
        f"- **File:** `{html.escape(component or 'Unknown')}`",
        f"- **Lines:** {line_display}",
        f"- **Effort to fix:** {html.escape(str(finding.get('effort', 'Not provided')))}",
    ]
    if finding.get("debt"):
        metadata.append(f"- **Technical debt:** {html.escape(str(finding['debt']))}")
    if tags:
        metadata.append(f"- **Tags:** {', '.join(f'`{html.escape(str(tag))}`' for tag in tags)}")
    if impact_display:
        metadata.append(f"- **Impacts:** {html.escape(impact_display)}")
    if rule.get("name"):
        metadata.append(f"- **Rule name:** {html.escape(str(rule['name']))}")
    if rule.get("cleanCodeAttribute"):
        metadata.append(f"- **Clean Code attribute:** {html.escape(str(rule['cleanCodeAttribute']))}")

    sections = [
        f"<!-- sonar-issue-key:{issue_key} -->",
        "Automated report from the SonarQube scan. This issue includes the finding context and source excerpt for implementation without opening SonarQube.",
        "",
        "## Classification and location",
        *metadata,
        f"- **SonarQube finding:** {issue_url}",
    ]
    if source_url:
        sections.append(f"- **Source at scanned commit:** {source_url}")
    sections.extend([
        "",
        "**Finding**",
        "",
        f"<pre>{html.escape(str(message))}</pre>",
        "",
        "## Source context",
        source_excerpt(finding.get("component", ""), project_key, finding),
    ])
    if rule_description:
        sections.extend(["", "## Rule guidance", "", rule_description])
    flow_text = flow_details(finding, project_key)
    if flow_text:
        sections.extend(["", "## Data flow locations", "", flow_text])
    return title, "\n".join(sections)


def sync_findings() -> tuple[int, int, int]:
    sonar_url = os.environ["SONAR_HOST_URL"].rstrip("/")
    sonar_token = os.environ["SONAR_TOKEN"]
    github_token = os.environ["GH_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]
    github_api = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    commit_sha = os.environ.get("GITHUB_SHA", "")
    project_key = project_key_from_config()

    findings = fetch_findings(sonar_url, sonar_token, project_key)
    existing = fetch_existing_issues(github_api, github_token, repository)
    repository_path = quote(repository, safe="/")
    label_specs = {
        name: (name, color, description)
        for finding in findings
        for name, color, description in finding_labels(finding)
    }
    if label_specs:
        ensure_repository_labels(github_api, github_token, repository_path, list(label_specs.values()))

    rules = {}
    created = updated = unchanged = 0

    for finding in findings:
        issue_key = finding["key"]
        rule_key = finding.get("rule", "")
        if rule_key and rule_key not in rules:
            try:
                rules[rule_key] = rule_details(sonar_url, sonar_token, rule_key)
            except RuntimeError as error:
                print(f"Warning: could not fetch SonarQube rule details for {rule_key}: {error}")
                rules[rule_key] = {}
        issue_labels = finding_labels(finding)
        title, body = issue_content(
            finding,
            project_key,
            sonar_url,
            rule=rules.get(rule_key, {}),
            repository=repository,
            commit_sha=commit_sha,
        )
        tracked = existing.get(issue_key)
        if tracked is None:
            tracked = request_json(
                f"{github_api}/repos/{repository_path}/issues",
                github_token,
                github=True,
                method="POST",
                payload={"title": title, "body": body},
            )
            created += 1
        else:
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

        labels_changed = sync_issue_labels(
            github_api,
            github_token,
            repository_path,
            tracked,
            issue_labels,
        )
        if existing.get(issue_key) is not None and (updates or labels_changed):
            updated += 1
        elif existing.get(issue_key) is not None:
            unchanged += 1

    print(
        f"SonarQube findings: {len(findings)} unresolved; "
        f"GitHub issues created={created}, updated/reopened={updated}, unchanged={unchanged}."
    )
    return created, updated, unchanged


if __name__ == "__main__":
    sync_findings()