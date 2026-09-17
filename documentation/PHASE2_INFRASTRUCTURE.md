# Phase 2: Docker Infrastructure & Base Runtime Architecture

## 1. Executive Summary

Phase 2 establishes the containerized infrastructure topology and configuration baseline for the entire NOC platform. In production environments, running all services in an unsegmented container network or without health check dependencies leads to race conditions, security vulnerabilities, and cascading restart loops.

The Phase 2 architecture enforces:
1. **Network Segmentation**: Isolates internal telemetry and database communications from public ingress.
2. **Persistent Storage**: Retains metrics, alerts, dashboards, and log chunks across container rebuilds.
3. **Healthcheck-Driven Dependency Gates**: Prevents consumer services (like Grafana or Promtail) from initializing before their upstream dependencies (Prometheus or Loki) are healthy.
4. **Dual-Mode Portability**: Fully compatible with both Docker Compose and standalone Native execution.

---

## 2. Component Deep Dive (The 5-Question Framework)

### 1. Docker Compose Network Segmentation
- **WHAT**: Three discrete bridge networks: `noc-public`, `noc-telemetry`, and `noc-backend-net`.
- **WHY**: Security and blast-radius containment. Attackers breaching an externally reachable web server or dashboard should not have direct L3/L4 network access to the TSDB storage or internal alert webhooks.
- **HOW**: Docker bridge networks assign isolated virtual subnets. Containers can only communicate if they share membership in the same network:
  - `noc-public`: Grafana (3000), Prometheus UI (9090), and FastAPI public ingress (8000).
  - `noc-telemetry`: Exporters (9100, 9115), Promtail, Prometheus scraper, and Loki.
  - `noc-backend-net`: FastAPI backend, Alertmanager, and Database.
- **CONNECTION**: Prometheus connects to both `noc-telemetry` (to scrape exporters) and `noc-public` (for user queries). FastAPI connects to `noc-backend-net` (for internal alerts) and `noc-public` (for REST API calls).
- **NOC USAGE**: Ensures zero packet leakage and protects internal metrics from unauthorized external tampering.

### 2. Container Healthcheck Gates
- **WHAT**: Docker-level probes (`test: ["CMD-SHELL", "..."]`) that query the internal health API of each container (e.g., `http://localhost:9090/-/healthy`).
- **WHY**: In distributed systems, a container entering the `RUNNING` state does not mean the application inside is ready to accept traffic. If Grafana starts before Prometheus initializes its TSDB index, dashboards fail to load.
- **HOW**: Compose uses `depends_on: { service: { condition: service_healthy } }`. Docker polls the healthcheck command every 10s until 3 consecutive successes occur before unblocking downstream services.
- **CONNECTION**: Enforces startup ordering: `Prometheus (Healthy)` + `Loki (Healthy)` $\to$ `Grafana Starts`.
- **NOC USAGE**: Eliminates false-positive "Service Down" alerts during maintenance or platform boot.

### 3. Persistent Volumes & Data Retention
- **WHAT**: Docker named volumes mapped to disk: `prometheus_data`, `alertmanager_data`, `loki_data`, and `grafana_data`.
- **WHY**: By default, container storage is ephemeral. If a container crashes or is upgraded, unmounted data is lost forever.
- **HOW**: Data directories (`/prometheus`, `/loki`, `/var/lib/grafana`) are mounted to host-managed volume drivers.
- **CONNECTION**: Ensures that 15-day metric retention in Prometheus and 30-day log retention in Loki survive host reboots.
- **NOC USAGE**: Preserves historical trend baselines, SLA logs, and past incident records.

---

## 3. Configuration Inventory

| Service | Image | Port | Config Location | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Prometheus** | `prom/prometheus:v2.51.0` | `9090` | `configs/prometheus/prometheus.yml` | TSDB, metrics scraping, alert rules |
| **Alertmanager** | `prom/alertmanager:v0.27.0` | `9093` | `configs/alertmanager/alertmanager.yml` | Inhibit rules, group timers, webhooks |
| **Loki** | `grafana/loki:2.9.5` | `3100` | `configs/loki/loki-config.yml` | Compressed log storage & LogQL |
| **Promtail** | `grafana/promtail:2.9.5` | N/A | `configs/promtail/promtail-config.yml` | File log tailing & shipping |
| **Grafana** | `grafana/grafana:10.4.0` | `3000` | `configs/grafana/provisioning/` | Auto-provisioned single pane of glass |
| **Node Exporter** | `prom/node-exporter:v1.7.0` | `9100` | Default OS metrics | Host OS CPU/RAM/Disk telemetry |
| **Blackbox Exporter**| `prom/blackbox-exporter:v0.24.0` | `9115` | `configs/blackbox/blackbox.yml` | Synthetic ICMP/HTTP/DNS probes |
| **NOC Backend** | Custom Python 3.11 Image | `8000` | `docker/Dockerfile.backend` | FastAPI orchestrator & AI engine |

---

## 4. Verification Checkpoint

Execute the Phase 2 audit script to verify all container definitions, volume mappings, and YAML syntax:

```bash
python scripts/verify_phase2.py
```
