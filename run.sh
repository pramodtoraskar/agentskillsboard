#!/usr/bin/env bash
set -e

echo "=== Agent Skills Board — Setup ==="

# Check Python ≥3.11 requirement
python3 -c "import sys; sys.exit(0 if (sys.version_info.major > 3 or (sys.version_info.major == 3 and sys.version_info.minor >= 11)) else 1)" || {
  echo "Python 3.11+ required, found $(python3 -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")')"
  exit 1
}

# Create venv if not exists
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "✓ Created virtualenv"
fi

source .venv/bin/activate

# Install deps
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Ensure data dir exists
mkdir -p data

# Run crawler first if no data
if [ ! -f "data/skills.json" ]; then
  echo ""
  echo "=== First run: crawling GitHub for SKILL.md files ==="
  echo "Set GITHUB_TOKEN env var for higher rate limits (5000/hr vs 60/hr):"
  echo "  export GITHUB_TOKEN=ghp_your_token_here"
  echo ""
  python3 crawler.py
  python3 normalizer.py
fi

echo ""
echo "=== Agent Skills Board — Starting ==="
echo "→ Dashboard: http://localhost:8000"
echo ""

python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
