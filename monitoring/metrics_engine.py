#!/usr/bin/env python3
"""
NOC Prometheus Metrics Engine
Simulates and exports production-grade enterprise telemetry for:
- Core routers, distribution switches, firewalls
- Server fleet (CPU, RAM, Disk, Load) via real psutil and simulated nodes
- Network quality (Latency, Packet Loss, Bandwidth)
- Application performance & synthetic health probes
- NOC Incident & Alert counters for Grafana Executive Dashboards

Conforms to Prometheus Exposition Format.
"""

import time
import random
import threading
from typing import Dict, Any

from prometheus_client import (
    start_http_server,
    Gauge,
    Counter,
    Histogram,
    REGISTRY
)
import psutil

# ==============================================================================
# 1. METRIC DEFINITIONS
# ==============================================================================

# Executive & Fleet Summary
OVERALL_HEALTH = Gauge(
    'noc_overall_health_percent',
    'Overall operational health percentage of all infrastructure and services (0-100)'
)
ACTIVE_INCIDENTS = Gauge(
    'noc_active_incidents',
    'Count of currently open incidents by severity',
    ['severity']
)
CRITICAL_ALERTS = Gauge(
    'noc_critical_alerts_total',
    'Total number of actively firing critical alerts'
)

# Network Devices Telemetry
DEVICE_STATUS = Gauge(
    'noc_device_status',
    'Status of network device (1 = ONLINE, 0 = OFFLINE)',
    ['device', 'type', 'role', 'site']
)
NETWORK_LATENCY = Gauge(
    'noc_network_latency_ms',
    'Network round-trip latency to device in milliseconds',
    ['target', 'tier']
)
PACKET_LOSS = Gauge(
    'noc_network_packet_loss_percent',
    'Network packet loss percentage (0-100)',
    ['target', 'tier']
)
BANDWIDTH_IN = Gauge(
    'noc_network_bandwidth_in_bytes',
    'Inbound bandwidth rate on interface in bytes/sec',
    ['device', 'interface']
)
BANDWIDTH_OUT = Gauge(
    'noc_network_bandwidth_out_bytes',
    'Outbound bandwidth rate on interface in bytes/sec',
    ['device', 'interface']
)

# Host & Server Fleet Telemetry
SERVER_HEALTH = Gauge(
    'noc_server_health',
    'Health status of server host (1 = HEALTHY, 0 = DEGRADED/OFFLINE)',
    ['server', 'tier']
)
HOST_CPU_UTIL = Gauge(
    'noc_host_cpu_utilization_percent',
    'CPU utilization percentage of host',
    ['instance']
)
HOST_MEM_UTIL = Gauge(
    'noc_host_memory_utilization_percent',
    'Memory utilization percentage of host',
    ['instance']
)
HOST_DISK_UTIL = Gauge(
    'noc_host_disk_utilization_percent',
    'Root disk utilization percentage of host',
    ['instance']
)

# Application & Database Telemetry
APP_HEALTH = Gauge(
    'noc_application_health',
    'Application endpoint availability (1 = UP, 0 = DOWN)',
    ['app', 'endpoint']
)
APP_LATENCY = Gauge(
    'noc_application_response_time_seconds',
    'HTTP API response time in seconds',
    ['app', 'endpoint']
)
DB_POOL_UTIL = Gauge(
    'noc_db_connection_pool_utilization_percent',
    'Database connection pool utilization percentage',
    ['database']
)
PROBE_SUCCESS = Gauge(
    'probe_success',
    'Synthetic Blackbox probe result (1 = SUCCESS, 0 = FAILURE)',
    ['instance', 'probe_type']
)

# ==============================================================================
# 2. INFRASTRUCTURE FLEET TOPOLOGY
# ==============================================================================

NETWORK_DEVICES = [
    {"device": "rtr-core-01", "type": "router", "role": "core-backbone", "site": "dc-primary", "ip": "10.0.0.1"},
    {"device": "rtr-edge-02", "type": "router", "role": "wan-edge", "site": "dc-primary", "ip": "10.0.0.2"},
    {"device": "sw-dist-01", "type": "switch", "role": "distribution", "site": "dc-primary", "ip": "10.0.1.1"},
    {"device": "sw-dist-02", "type": "switch", "role": "distribution", "site": "dc-primary", "ip": "10.0.1.2"},
    {"device": "fw-perimeter-01", "type": "firewall", "role": "edge-security", "site": "dc-primary", "ip": "10.0.2.1"},
]

SERVER_FLEET = [
    {"server": "srv-web-01", "tier": "frontend", "cpu_base": 35.0, "mem_base": 55.0},
    {"server": "srv-web-02", "tier": "frontend", "cpu_base": 38.0, "mem_base": 52.0},
    {"server": "srv-api-01", "tier": "application", "cpu_base": 45.0, "mem_base": 65.0},
    {"server": "srv-api-02", "tier": "application", "cpu_base": 42.0, "mem_base": 63.0},
    {"server": "srv-db-primary", "tier": "database", "cpu_base": 55.0, "mem_base": 78.0},
    {"server": "srv-cache-01", "tier": "cache", "cpu_base": 20.0, "mem_base": 45.0},
]

APPLICATIONS = [
    {"app": "web-frontend", "endpoint": "https://portal.enterprise.local", "base_lat": 0.045},
    {"app": "order-api", "endpoint": "https://api.enterprise.local/orders", "base_lat": 0.080},
    {"app": "auth-service", "endpoint": "https://auth.enterprise.local/oauth", "base_lat": 0.030},
    {"app": "payment-gw", "endpoint": "https://pay.enterprise.local/v1/charge", "base_lat": 0.120},
]

# Fault Injection State Matrix
INJECTED_FAULTS: Dict[str, Any] = {}

# ==============================================================================
# 3. TELEMETRY COLLECTION & SIMULATION LOOP
# ==============================================================================

class NOCMetricsCollector:
    def __init__(self):
        self.running = False

    def update_telemetry(self):
        """Generates realistic telemetry points based on fleet state and faults."""
        total_entities = 0
        healthy_entities = 0

        # 1. Update Network Devices
        for dev in NETWORK_DEVICES:
            d_name = dev["device"]
            total_entities += 1
            if INJECTED_FAULTS.get(d_name) == "OFFLINE":
                DEVICE_STATUS.labels(device=d_name, type=dev["type"], role=dev["role"], site=dev["site"]).set(0)
                NETWORK_LATENCY.labels(target=d_name, tier=dev["role"]).set(999.0)
                PACKET_LOSS.labels(target=d_name, tier=dev["role"]).set(100.0)
                BANDWIDTH_IN.labels(device=d_name, interface="eth0").set(0)
                BANDWIDTH_OUT.labels(device=d_name, interface="eth0").set(0)
            else:
                healthy_entities += 1
                DEVICE_STATUS.labels(device=d_name, type=dev["type"], role=dev["role"], site=dev["site"]).set(1)
                latency = round(random.uniform(1.2, 4.8), 2)
                loss = 0.0 if random.random() > 0.05 else round(random.uniform(0.1, 0.4), 2)
                NETWORK_LATENCY.labels(target=d_name, tier=dev["role"]).set(latency)
                PACKET_LOSS.labels(target=d_name, tier=dev["role"]).set(loss)
                BANDWIDTH_IN.labels(device=d_name, interface="eth0").set(random.randint(15_000_000, 45_000_000))
                BANDWIDTH_OUT.labels(device=d_name, interface="eth0").set(random.randint(20_000_000, 60_000_000))

        # 2. Update Server Fleet
        # Include actual host psutil metrics for host representation
        try:
            real_cpu = psutil.cpu_percent(interval=None)
            real_mem = psutil.virtual_memory().percent
            real_disk = psutil.disk_usage("/").percent
        except Exception:
            real_cpu, real_mem, real_disk = 25.0, 45.0, 50.0

        for srv in SERVER_FLEET:
            s_name = srv["server"]
            total_entities += 1
            if INJECTED_FAULTS.get(s_name) == "CPU_SPIKE":
                cpu_val = round(random.uniform(92.0, 99.5), 1)
                mem_val = srv["mem_base"] + random.uniform(-2, 3)
                SERVER_HEALTH.labels(server=s_name, tier=srv["tier"]).set(0)
            elif INJECTED_FAULTS.get(s_name) == "MEM_EXHAUSTION":
                cpu_val = srv["cpu_base"] + random.uniform(-3, 3)
                mem_val = round(random.uniform(94.0, 98.5), 1)
                SERVER_HEALTH.labels(server=s_name, tier=srv["tier"]).set(0)
            elif INJECTED_FAULTS.get(s_name) == "DOWN":
                cpu_val, mem_val = 0.0, 0.0
                SERVER_HEALTH.labels(server=s_name, tier=srv["tier"]).set(0)
            else:
                healthy_entities += 1
                # Blend realistic variation
                cpu_val = max(5.0, min(80.0, srv["cpu_base"] + random.uniform(-8.0, 8.0)))
                mem_val = max(10.0, min(85.0, srv["mem_base"] + random.uniform(-3.0, 3.0)))
                SERVER_HEALTH.labels(server=s_name, tier=srv["tier"]).set(1)

            HOST_CPU_UTIL.labels(instance=s_name).set(cpu_val)
            HOST_MEM_UTIL.labels(instance=s_name).set(mem_val)
            HOST_DISK_UTIL.labels(instance=s_name).set(real_disk)

        # 3. Update Application Endpoints & Synthetic Probes
        for app in APPLICATIONS:
            a_name = app["app"]
            total_entities += 1
            if INJECTED_FAULTS.get(a_name) == "OUTAGE":
                APP_HEALTH.labels(app=a_name, endpoint=app["endpoint"]).set(0)
                APP_LATENCY.labels(app=a_name, endpoint=app["endpoint"]).set(5.0)
                PROBE_SUCCESS.labels(instance=app["endpoint"], probe_type="http_2xx").set(0)
            else:
                healthy_entities += 1
                APP_HEALTH.labels(app=a_name, endpoint=app["endpoint"]).set(1)
                lat = round(app["base_lat"] + random.uniform(-0.005, 0.015), 4)
                APP_LATENCY.labels(app=a_name, endpoint=app["endpoint"]).set(lat)
                PROBE_SUCCESS.labels(instance=app["endpoint"], probe_type="http_2xx").set(1)

        # 4. Database Connection Pool
        if INJECTED_FAULTS.get("srv-db-primary") == "POOL_EXHAUSTED":
            DB_POOL_UTIL.labels(database="postgres_production").set(98.5)
        else:
            DB_POOL_UTIL.labels(database="postgres_production").set(round(random.uniform(25.0, 48.0), 1))

        # 5. Incident & High-Level KPIs
        active_critical = sum(1 for v in INJECTED_FAULTS.values() if v in ["OFFLINE", "DOWN", "OUTAGE", "POOL_EXHAUSTED"])
        active_high = sum(1 for v in INJECTED_FAULTS.values() if v in ["CPU_SPIKE", "MEM_EXHAUSTION"])

        ACTIVE_INCIDENTS.labels(severity="critical").set(active_critical)
        ACTIVE_INCIDENTS.labels(severity="high").set(active_high)
        ACTIVE_INCIDENTS.labels(severity="warning").set(1 if random.random() > 0.7 else 0)
        CRITICAL_ALERTS.set(active_critical)

        # Overall Health Ratio
        health_pct = round((healthy_entities / max(1, total_entities)) * 100.0, 1)
        OVERALL_HEALTH.set(health_pct)

    def run_loop(self, interval: float = 3.0):
        self.running = True
        while self.running:
            self.update_telemetry()
            time.sleep(interval)

    def stop(self):
        self.running = False


# Global Collector Instance
collector = NOCMetricsCollector()

def start_metrics_server(port: int = 9090):
    """Starts Prometheus metrics exposition server in background thread."""
    print(f"[*] Starting Prometheus Metrics Engine on http://0.0.0.0:{port}/metrics")
    start_http_server(port)
    t = threading.Thread(target=collector.run_loop, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9090
    print("=========================================================")
    print(f" NOC Prometheus Metrics Engine - Listening on port {port}")
    print("=========================================================")
    server_thread = start_metrics_server(port)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Metrics Engine...")
        collector.stop()
