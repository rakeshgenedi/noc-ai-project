#!/usr/bin/env python3
"""
NOC Port Conflict Detection Script
Verifies whether default ports required by NOC services are available.
Zero external dependencies.
"""

import socket
import sys

NOC_SERVICES = [
    {"name": "Prometheus Server", "port": 9090, "desc": "Time-series metrics collector"},
    {"name": "Alertmanager", "port": 9093, "desc": "Alert routing & deduplication"},
    {"name": "Grafana Dashboard", "port": 3000, "desc": "NOC visualization UI"},
    {"name": "Loki Log Engine", "port": 3100, "desc": "Log ingestion & query engine"},
    {"name": "Node Exporter", "port": 9100, "desc": "Host system metrics exporter"},
    {"name": "FastAPI NOC Backend", "port": 8000, "desc": "Alert receiver & AI incident triage"},
    {"name": "Blackbox Exporter", "port": 9115, "desc": "Network probe & latency exporter"},
]

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        result = s.connect_ex((host, port))
        return result == 0

def main():
    print("\n" + "=" * 65)
    print(" [NOC PORT AUDIT] Checking Availability for Core Services")
    print("=" * 65)
    
    conflicts = 0
    for svc in NOC_SERVICES:
        in_use = is_port_in_use(svc["port"])
        if in_use:
            print(f"  [CONFLICT] Port {svc['port']:<5} ({svc['name']}) is ALREADY IN USE!")
            print(f"             Description: {svc['desc']}")
            conflicts += 1
        else:
            print(f"  [AVAILABLE] Port {svc['port']:<5} ({svc['name']}) is FREE.")

    print("=" * 65)
    if conflicts == 0:
        print("  PORT STATUS: [ALL CLEAR] All required NOC service ports are free!")
        return 0
    else:
        print(f"  PORT STATUS: [WARNING] {conflicts} port(s) currently occupied.")
        print("  Action: Check running processes or adjust port mappings in .env.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
