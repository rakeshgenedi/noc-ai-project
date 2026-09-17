# Phase 3: Core Metrics & Visualization (Prometheus + Grafana)

## 1. Executive Summary

Phase 3 implements the heart of the monitoring tier: the **Prometheus Metrics Engine**, production **Alerting Rules**, and the **NOC Overview Dashboard (Dashboard 1)** in Grafana.

In high-stakes enterprise operations, raw metrics without strict dimensional labeling are useless. Phase 3 enforces standard multi-dimensional label taxonomies (`device`, `type`, `role`, `tier`, `instance`, `site`) and wires them directly into executive gauges, network latency trendlines, and automated alert triggers.

---

## 2. Component Deep Dive (The 5-Question Framework)

### 1. Prometheus Time-Series Database (TSDB) & PromQL
- **WHAT**: A high-efficiency time-series engine that stores metric streams as timestamped float64 samples with key-value label pairs.
- **WHY**: A NOC requires microsecond-level query speed across historical data to evaluate SLOs, error budgets, and sudden trend inversions.
- **HOW**: Prometheus samples metrics at regular intervals (15s default). It utilizes custom chunk compression (XOR delta-of-delta timestamp and value compression) capable of packing millions of samples into megabytes of RAM. PromQL functions like `rate()`, `avg()`, and `histogram_quantile()` transform raw counter increments into per-second rates.
- **CONNECTION**: Scrapes targets on port 9090/9100; evaluates rule files every 15s; dispatches firing alerts to Alertmanager on port 9093.
- **NOC USAGE**: Analysts use PromQL in Grafana or the Prometheus expression browser to investigate spikes (e.g., `rate(node_network_receive_bytes_total[5m])`).

### 2. Prometheus Alerting Rules Engine
- **WHAT**: Continuous evaluation of boolean PromQL threshold statements defined in [alerts/noc_infrastructure_rules.yml](file:///c:/Users/RAKESH%20GENEDI/Downloads/noc-ai-project/alerts/noc_infrastructure_rules.yml).
- **WHY**: Without automated threshold rules, engineers would have to watch hundreds of dashboard graphs manually 24/7.
- **HOW**: Prometheus evaluates the `expr:` clause every evaluation cycle (15s). If the expression holds true for the duration specified in `for:` (e.g., `for: 2m`), the alert transitions from `PENDING` to `FIRING` and is dispatched to Alertmanager.
- **CONNECTION**: Routes firing alarms with labels (`severity="critical"`, `tier="network"`) and annotations (summary, description, runbook URL) to Alertmanager.
- **NOC USAGE**: Serves as the primary operational tripwire. Alerts page the on-call engineer and trigger automated ticket creation.

### 3. Grafana Dashboard 1: NOC Overview
- **WHAT**: Executive single-pane-of-glass dashboard ([dashboard/01_noc_overview.json](file:///c:/Users/RAKESH%20GENEDI/Downloads/noc-ai-project/dashboard/01_noc_overview.json)) tracking fleet health, open incidents, and performance across Network, Server, and Application tiers.
- **WHY**: Tier 1 NOC analysts and Incident Commanders need an immediate 5-second situational awareness summary of global infrastructure health without navigating through dozens of separate tabs.
- **HOW**: Built using 14 modular visual panels:
  - **KPI Row**: System Health Gauge, Devices Online/Total Stat, Open Incidents Stat, Critical Alarms Stat.
  - **Fleet Status Row**: Network Device Bar Gauges, Host Fleet Health, Application Availability.
  - **Real-Time Telemetry Row**: Core Network Latency Line Charts, Packet Loss Gauges, CPU Utilization, and API Latency.
- **CONNECTION**: Queries Prometheus TSDB directly using PromQL proxy endpoints.
- **NOC USAGE**: Displayed on 24/7 video walls in enterprise operations centers; color-coded thresholds (Red/Yellow/Green) immediately highlight failing regions or clusters.

---

## 3. PromQL Mathematical Foundations

### Rate Calculation on Monotonic Counters
A counter (such as total packets or CPU seconds) always increments and never decreases (except on system reboot). To calculate per-second rate over a time window $\Delta t$:
$$\text{rate}(v[1m]) = \frac{v(t) - v(t - \Delta t)}{\Delta t}$$
Prometheus automatically compensates for counter resets (reboots).

### Host CPU Utilization Calculation
```promql
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)
```
This formula calculates the percentage of non-idle CPU cycles over a 2-minute sliding window across each distinct host instance.

---

## 4. Verification Checkpoint

Execute the Phase 3 verification suite:

```bash
python scripts/verify_phase3.py
```
