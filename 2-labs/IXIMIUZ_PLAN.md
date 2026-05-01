# Iximiuz Labs Learning Plan

This document serves as the architectural blueprint for other agents and developers working on this project. It outlines how the "Learning Labs" in this repository are designed to leverage the **iximiuz Labs** platform.

## What is iximiuz Labs?
[iximiuz Labs](https://labs.iximiuz.com/) provides browser-based, short-lived Linux and Kubernetes playgrounds. Because these are true Linux VMs (often Ubuntu-based), they bypass many of the common volume-mounting and networking friction points found in local Windows/Mac Docker Desktop setups.

## Recommended Playgrounds for Learning

Based on the labs provided in this repository, here are the exact iximiuz playgrounds you should use:

### 1. Docker Compose Labs (No-K8s)
- **Goal:** Learn ELK and Prometheus/Grafana fundamentals using `docker-compose`.
- **Recommended Playground:** `docker` or `ubuntu`
- **Why:** These playgrounds come pre-installed with the Docker engine and `docker-compose`. Since they are Linux VMs, we can seamlessly mount host directories like `/var/lib/docker/containers` into our log shippers (like Fluent Bit) without worrying about Windows WSL2 permission issues.

### 2. Kubernetes Labs
- **Goal:** Learn PLG (Promtail/Loki/Grafana) and EFK stacks in a cloud-native K8s environment.
- **Recommended Playground:** `k3s` (Single or Multi-node)
- **Why:** K3s provides a lightweight, fully conformant Kubernetes environment. It comes with `kubectl` and `helm` pre-configured.

## Networking and Port Exposure Rules
A critical feature of iximiuz Labs is the ability to expose ports to the public internet via their Web UI or `labctl`. 

**CRITICAL INSTRUCTION FOR AGENTS:** 
To expose a service in iximiuz, the service **must** bind to all interfaces (`0.0.0.0`). Binding to `localhost` or `127.0.0.1` will prevent the "Expose Port" button from working.

- **Docker Compose:** Use `ports: - "5601:5601"` (this naturally binds to `0.0.0.0`).
- **Kubernetes:** When port-forwarding a service, you MUST use the `--address 0.0.0.0` flag.
  - *Example:* `kubectl port-forward --address 0.0.0.0 -n monitoring svc/kibana 5601:5601`

## Repository Structure for Labs

The repository is organized to support this learning simulator approach:

1. **`docker-compose-elk.yml`**: Standalone Compose file for ELK. Fluent Bit mounts `/var/lib/docker/containers`.
2. **`docker-compose-prom.yml`**: Standalone Compose file for Prometheus and Grafana.
3. **`3-kubernetes/observability/`**: K8s manifests for PLG and EFK stacks.
4. **`scripts/setup/learning-lab.sh`**: The master orchestration script to tear down and spin up different environments.
5. **`scripts/deploy/deploy-observability.sh`**: The K8s specific deployer (updated to support `0.0.0.0` port forwarding).

---
*Note for AI Agents: Always consult this file before making modifications to the networking or volume mounting structures in the Docker or Kubernetes manifests. Ensure compatibility with the standard Linux capabilities provided by iximiuz.*
