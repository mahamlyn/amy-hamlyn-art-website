# Website Deployment & Runner Documentation

This document records the package versions, tooling, deployment setup, and project onboarding details for the Amy Hamlyn Art website.

> The active deployment workflow is Cloudflare Pages via [`.github/workflows/build.yml`](../.github/workflows/build.yml). It deploys the static export to the `amyhamlynart` project after the build and SonarQube Quality Gate pass.

## 1. SonarQube onboarding summary

This project was configured in SonarQube as a Python project, using the Python language selection during onboarding.

### Why Python was selected

The project is a Flask application built with Python, as confirmed by:

- [app.py](../app.py) — Flask application and route definitions
- [requirements.txt](../requirements.txt) — Python dependencies including Flask, Markdown, and PyYAML

The site is therefore best classified as a Python web application rather than a JavaScript or generic static site.

### SonarQube project setup

During SonarQube onboarding, the project was described as:

- Project type: Python
- Tech stack: Flask + Python
- Repository: GitHub
- CI/CD: GitHub Actions / self-hosted runner model

### Recommended onboarding choices

When asked to describe the project in SonarQube, select:

- Python

This matches the project architecture and ensures the correct rules and language coverage are applied.

### CI pipeline status

A build, SonarQube scan, and Cloudflare Pages deployment pipeline runs only when manually started from GitHub Actions. The SonarQube job uses a self-hosted runner; deployment runs on a GitHub-hosted runner.

The current workflow file is:

- [.github/workflows/build.yml](../.github/workflows/build.yml)

The workflow triggers are:

```yaml
on:
  workflow_dispatch:
```

The manually started workflow builds the static site, runs SonarQube analysis and the Quality Gate, then deploys the build artifact to Cloudflare Pages only when both earlier jobs succeed.

After the analysis completes, `scripts/sync_sonar_issues.py` creates one GitHub issue per unresolved SonarQube finding. It uses the SonarQube issue key to update or reopen an existing issue on later runs instead of creating duplicates. The scan job requires `issues: write` for `GITHUB_TOKEN`; the SonarQube token must be able to browse the configured project.

The static export is produced by `scripts/build_static_site.py` with `PAGES_BASE_PATH=/`; no Cloudflare build command is needed in the Cloudflare dashboard because GitHub Actions performs the build and deployment.

The workflow uses the SonarQube scanner action with the following environment variables:

```yaml
env:
  SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

These values must be set as GitHub repository secrets for the project to authenticate with the SonarQube server.

### SonarQube exclusion configuration

The project configuration includes exclusions for generated or utility script paths:

- [sonar-project.properties](../sonar-project.properties)

Current configuration:

```properties
sonar.projectKey=amy-hamlyn-art-website
sonar.exclusions=src/**,**/scripts/**
```

This excludes files in any `scripts` directory from SonarQube analysis.

---

## 2. Website application dependencies

The current site is a Flask-based application. The Python dependencies are defined in [requirements.txt](../requirements.txt) and are currently:

- Flask==3.1.0
- markdown==3.7
- PyYAML==6.0.2

These packages are required for the local development environment and for any build or static-render step before deploying to Cloudflare.

### Install command

```bash
python -m venv .venv
. .venv/bin/activate  # Linux/macOS
# or: .\.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

### Relevant project files

- [app.py](../app.py) — Flask application and route definitions
- [requirements.txt](../requirements.txt) — Python package list
- [README.md](../README.md) — site overview and local run instructions

---

## 2. Cloudflare Pages prerequisites

Create or use the Cloudflare Pages project named `amyhamlynart`. In GitHub repository settings, add these Actions secrets:

- `CLOUDFLARE_API_TOKEN` — token with permission to edit Cloudflare Pages projects
- `CLOUDFLARE_ACCOUNT_ID` — Cloudflare account that owns the Pages project
- `SONAR_TOKEN` and `SONAR_HOST_URL` — required for the security scan

The deployment action runs Wrangler on a GitHub-hosted runner, so Node.js and Wrangler do not need to be installed on the self-hosted SonarQube runner. The site is built as static files because Cloudflare Pages does not run this Flask application directly.

---

## 3. Deployment model for this project

This website runs as a Flask application locally and is exported to static output for Cloudflare Pages by `scripts/build_static_site.py`.

### Why this matters

The main app in [app.py](../app.py) is a Python server that renders templates and loads Markdown content at runtime. Cloudflare Pages does not run Flask directly for this app without a build/export layer.

### Deployment flow

1. GitHub Actions installs Python dependencies and generates `dist/`.
2. SonarQube scan and Quality Gate must pass.
3. Wrangler deploys `dist/` to the `amyhamlynart` project on the `main` production branch.

---

## 4. Recommended Cloudflare environment variables

Set these in the GitHub Actions repository secrets:

- CLOUDFLARE_API_TOKEN
- CLOUDFLARE_ACCOUNT_ID

The workflow uses the fixed Pages project name `amyhamlynart` and deploys the `main` branch.

### Example GitHub Actions configuration

```yaml
env:
  CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
  CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

---

## 5. Deployment command

A practical deployment workflow for this site is:

```bash
python -m pip install -r requirements.txt
PAGES_BASE_PATH=/ python scripts/build_static_site.py
npx wrangler pages deploy dist --project-name amyhamlynart --branch main
```

In CI, the Cloudflare Wrangler action runs the deployment command after the build and security scan instead of requiring a local Wrangler installation.

---

## 6. Official documentation references

Use these references for setup and deployment guidance:

- Python packaging and environment setup: https://packaging.python.org/
- Flask documentation: https://flask.palletsprojects.com/
- Markdown package documentation: https://pypi.org/project/Markdown/
- PyYAML documentation: https://pyyaml.org/wiki/PyYAMLDocumentation
- Node.js LTS: https://nodejs.org/
- Wrangler CLI: https://developers.cloudflare.com/workers/wrangler/
- Cloudflare Pages: https://developers.cloudflare.com/pages/
- GitHub self-hosted runners: https://docs.github.com/en/actions/hosting-your-own-runners

---

## 7. Recommended baseline summary

For this website, the practical default package baseline is:

- Python 3.12
- Flask 3.1.0
- Markdown 3.7
- PyYAML 6.0.2
- Node.js 20 LTS
- Wrangler latest
- GitHub Actions self-hosted Linux runner

This setup builds the static site and deploys it to Cloudflare Pages after a successful SonarQube Quality Gate.
