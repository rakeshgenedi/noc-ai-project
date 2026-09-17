# AI-Assisted Network Operations Center (NOC) Platform

A practical, realistic Network Operations Center (NOC) monitoring and AI-assisted incident management platform.

## Architecture
- **Metrics Collection**: Prometheus & Node Exporter
- **Log Management**: Grafana Loki & Promtail
- **Visualization**: Grafana
- **Alert Management**: Prometheus Alertmanager
- **Incident Backend**: Python FastAPI & SQLite/PostgreSQL
- **AI Triage Engine**: Configurable LLM (Gemini / OpenAI / Ollama / Mock)
- **Notification Pipeline**: Webhook dispatcher (Discord/Slack/Teams/Email)

## Quick Start (Phase 1)
1. Run pre-flight verification:
   ```bash
   python scripts/verify_env.py
   python scripts/check_ports.py
   ```
2. Activate Virtual Environment:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
