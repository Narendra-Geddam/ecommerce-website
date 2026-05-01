# Lab 3: Kubernetes PLG Stack

## Overview
This lab covers the PLG (Promtail, Loki, Grafana) stack running entirely inside Kubernetes. This is the modern, lightweight logging alternative to ELK. Promtail runs as a DaemonSet to scrape logs, Loki stores them, and Grafana visualizes them.

## Playground Requirements
- **Platform:** iximiuz Labs (https://labs.iximiuz.com/)
- **Playground Type:** `k3s` 
- **Why?** You need a fully functional Kubernetes cluster. The `k3s` playground provides a lightweight cluster with `kubectl` pre-configured.

## What to Install / Configure
The observability resources are defined as standard Kubernetes manifests.
Key files to study:
- `3-kubernetes/observability/loki-promtail-config.yaml`: Look at how `promtail` is deployed as a `DaemonSet`. Notice the volume mount for `/var/log`. This is how it accesses the logs of all pods running on that node.

## Execution Steps

1. Open your iximiuz `k3s` playground terminal.
2. Clone this repository and enter it.
3. Apply the base application first (so there are logs to capture):
   ```bash
   kubectl apply -k 3-kubernetes/base/
   ```
4. Start the observability lab using the orchestration script:
   ```bash
   ./2-labs/learning-lab.sh
   # Select option 4: Start K8s PLG Stack
   ```
   *Note: This script calls `deploy-observability.sh` and patches the port-forwarding to use `--address 0.0.0.0` which is required for iximiuz.*
5. Verify the pods are running in the `monitoring` namespace:
   ```bash
   kubectl get pods -n monitoring
   ```

## Working and Analysis (How to use it)

1. **Expose Grafana:**
   - In the iximiuz UI, click **Expose Port**.
   - Enter port `30030` (NodePort).
   - Click the generated URL to open the Grafana dashboard.
   - Login with **admin / admin**.

2. **Expose Prometheus (optional):**
   - Enter port `30090` (NodePort) to access the raw Prometheus UI.

3. **Analyze Logs in Grafana:**
   - Go to the **Explore** tab in Grafana (compass icon).
   - Ensure the data source dropdown is set to **Loki**.
   - Use LogQL (Loki Query Language) to search logs. 
   - **Example Queries:** 
     - `{namespace="prod-ecommerce"}` (Shows all logs from your app namespace)
     - `{app="ecommerce-backend"} |= "error"` (Finds the word "error" in backend logs)

## Teardown
When you are finished learning:
```bash
kubectl delete namespace monitoring
```
