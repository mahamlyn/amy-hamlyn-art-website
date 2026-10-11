# Website Deployment & Runner Documentation

This document records the package versions, tooling, deployment setup, and project onboarding details for the Amy Hamlyn Art website.

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

A SonarQube GitHub Actions pipeline has been enabled for this repository and is configured to run automatically on pushes to the main branch.

The current workflow file is:

- [.github/workflows/build.yml](../.github/workflows/build.yml)

The trigger is defined as:

```yaml
on:
  push:
    branches:
      - main
```

This means the analysis job runs whenever a commit is pushed to main.

The workflow uses the SonarQube scanner action with the following environment variables:

```yaml
env:
  SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

These values are expected to be set in the GitHub repository secrets for the project to authenticate with the SonarQube server.

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

## 2. Self-hosted runner requirements for Cloudflare deployment

The site is not a native Cloudflare Workers Python app. It is a Flask app with Markdown-driven content, so the deployment runner should be prepared to:

- install Python dependencies
- install Node.js and Wrangler
- run a static export or build step
- authenticate with Cloudflare
- deploy the generated static output to Cloudflare Pages

### Minimum runner tooling

Recommended versions for a Linux-based self-hosted GitHub Actions runner:

- Python: 3.12.x
- Node.js: 20.x LTS
- npm: bundled with Node.js 20
- Git: current stable release
- curl / ca-certificates / build-essential

### Example Linux installation

```bash
apt-get update
apt-get install -y curl git ca-certificates build-essential python3 python3-venv python3-pip
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install -g wrangler
```

### Cloudflare deployment package

Use the Wrangler CLI for deployment:

```bash
npm install -g wrangler@latest
```

This is the package used to authenticate and deploy a Cloudflare Pages project.

---

## 3. Deployment model for this project

This website currently runs as a Flask application locally, but Cloudflare Pages is best suited to static output. For this project, the runner should perform a static build/export before deployment.

### Why this matters

The main app in [app.py](../app.py) is a Python server that renders templates and loads Markdown content at runtime. Cloudflare Pages does not run Flask directly for this app without a build/export layer.

### Recommended deployment approach

1. install Python and site dependencies
2. generate a static website bundle from the markdown content
3. deploy the generated output to Cloudflare Pages
4. optionally use a minimal Worker only as a front-door or routing layer if needed

---

## 4. Recommended Cloudflare environment variables

Set these on the self-hosted runner or in the GitHub Actions secret store:

- CLOUDFLARE_API_TOKEN
- CLOUDFLARE_ACCOUNT_ID

Optional project-level values:

- PROJECT_NAME
- DEPLOY_BRANCH
- CUSTOM_DOMAIN

### Example GitHub Actions step

```yaml
env:
  CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
  CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

---

## 5. Typical runner workflow

A practical deployment workflow for this site is:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python build.py
npm install -g wrangler@latest
wrangler pages deploy dist --project-name amy-hamlyn-art
```

The exact build command depends on the static exporter script used for this project. At a minimum, the runner must be able to generate a deployable `dist/` or `site/` directory.

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

This setup is suitable for building and deploying the site to Cloudflare Pages after a static export step.
