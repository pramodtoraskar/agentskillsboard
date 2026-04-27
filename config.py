# config.py — single source of truth for all crawl targets
# Edit this file to add new orgs/repos. No code changes needed.

import os
import logging

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    logging.warning("WARNING: GITHUB_TOKEN not set. Rate limit: 60/hr vs 5000/hr. Crawling pinned repos only.")

# ── Tier 1: Official vendor orgs (highest trust score boost) ──────────────────
OFFICIAL_ORGS = [
    # Core AI orgs
    "anthropics",
    "openai",
    # Tool vendors
    "dbt-labs",
    "Snowflake-Labs",
    "DataDog",
    "atlassian",
    "salesforce",
    "servicenow",
    "hashicorp",
    "grafana",
    "apache",          # airflow, kafka, etc.
    "astronomer",      # airflow company with agent tools
    "mlflow",
    # Platform orgs
    "redhat-community-ai-tools",
    "openclaw",
    "datahub-project",
    "agentskills",
    # Role-based community
    "kubernetes",
    "cncf",
    "openSSF",
]

# ── Tier 2: Known repos with SKILL.md (pinned, crawl directly) ────────────────
# Format: "org/repo"  — crawled first before broad GitHub search
PINNED_REPOS = [
    "anthropics/skills",
    "openai/skills",
    "anthropics/claude-code",
    "agentskills/agentskills",
    "VoltAgent/awesome-openclaw-skills",
    "VoltAgent/awesome-agent-skills",
    "datahub-project/datahub-skills",
    "redhat-community-ai-tools/jira-mcp-snowflake",
    "win4r/OpenClaw-Skill",
    "sooperset/mcp-atlassian",
    "Snowflake-Labs/mcp",
    "wong2/awesome-mcp-servers",
    # Missing official skill repositories
    "dbt-labs/dbt-agent-skills",
    "astronomer/agents",
    "wshobson/agents",
]

# ── Role buckets — used to tag skills by audience ─────────────────────────────
ROLE_KEYWORDS = {
    "developer":  ["github", "git", "code", "pr", "pull-request", "ci", "cd", "pipeline",
                   "docker", "kubernetes", "k8s", "terraform", "helm", "deploy"],
    "data":       ["snowflake", "dbt", "airflow", "spark", "bigquery", "databricks",
                   "postgres", "sql", "etl", "pipeline", "dagster", "prefect"],
    "mlops":      ["mlflow", "kubeflow", "sagemaker", "model", "training", "inference",
                   "experiment", "registry", "serving", "monitoring", "drift"],
    "security":   ["cve", "nvd", "epss", "kev", "vuln", "sbom", "sigstore", "scorecard",
                   "snyk", "trivy", "owasp", "pentest", "sast", "dast"],
    "devops":     ["jira", "confluence", "servicenow", "pagerduty", "incident",
                   "alerting", "grafana", "datadog", "prometheus", "sre"],
    "analyst":    ["tableau", "powerbi", "looker", "metabase", "redash", "excel",
                   "csv", "report", "dashboard", "metric", "kpi"],
    "tester":     ["test", "pytest", "jest", "selenium", "playwright", "qa",
                   "coverage", "regression", "unit", "integration"],
    "designer":   ["figma", "sketch", "svg", "css", "ui", "ux", "design",
                   "prototype", "wireframe", "component", "storybook"],
    "architect":  ["architecture", "diagram", "c4", "mermaid", "adr", "rfc",
                   "system-design", "api", "openapi", "swagger", "grpc"],
}

# ── Scoring weights (must sum to 100) ─────────────────────────────────────────
SCORE_WEIGHTS = {
    "is_official":   35,   # org in OFFICIAL_ORGS
    "stars":         25,   # log-normalised GitHub stars
    "downloads":     15,   # if available (PyPI/npm)
    "recency":       15,   # days since last commit, decays
    "has_ci":         5,   # .github/workflows present
    "has_tests":      5,   # tests/ dir or pytest files present
}

# ── Crawler performance settings ──────────────────────────────────────────────
RATE_LIMIT_DELAY   = 0.5   # seconds between GitHub API calls
CACHE_TTL_HOURS    = 6     # re-use cached org member list for N hours
MAX_SEARCH_PAGES   = 5     # GitHub code-search pages (100 results each = 500 max)
DB_PATH            = "data/skills.json"
RAW_PATH           = "data/raw_skills.json"
