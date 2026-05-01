# Lab 4: Kubernetes EFK Stack

## Overview
This lab covers the enterprise-standard EFK (Elasticsearch, Fluent Bit, Kibana) stack running in Kubernetes. You will deploy Elasticsearch to index logs, Kibana to visualize them, and a Fluent Bit DaemonSet that reads Kubernetes log files from the node filesystem and forwards them to Elasticsearch.

## Playground Requirements
- **Platform:** iximiuz Labs (https://labs.iximiuz.com/)
- **Playground Type:** `k3s` 
- **Why?** You need a fully functional Kubernetes cluster.

## What to Install / Configure
The observability resources are defined as standard Kubernetes manifests.
Key files to study:
- `3-kubernetes/observability/efk-config.yaml`: Look at the `fluent-bit` DaemonSet. Notice how it mounts `/var/log` and `/var/lib/docker/containers` in read-only mode so it can scrape logs across all pods natively without interfering with them. Also notice the `fluent-bit-config` ConfigMap which tells Fluent Bit to use the `kubernetes` filter to enrich raw logs with K8s metadata (like pod names and namespaces).

## Execution Steps

1. Open your iximiuz `k3s` playground terminal.
2. Clone this repository and enter it.
3. Apply the base application first:
   ```bash
   kubectl apply -k 3-kubernetes/base/
   ```
4. Start the observability lab using the orchestration script:
   ```bash
   ./2-labs/learning-lab.sh
   # Select option 5: Start K8s EFK Stack
   ```
5. Verify the pods are running in the `monitoring` namespace:
   ```bash
   kubectl get pods -n monitoring
   ```
   *(Note: Elasticsearch might take a minute or two to become fully ready).*

## Working and Analysis (How to use it)

1. **Expose Kibana:**
   - In the iximiuz UI, click **Expose Port**.
   - Enter port `30056` (NodePort).
   - Click the generated URL to open the Kibana dashboard.

2. **Configure Index Pattern:**
   - In Kibana, click the hamburger menu (top left) -> **Stack Management** -> **Data Views** (or Index Patterns).
   - Click **Create Data View**.
   - Name it `fluent-bit-*` and set the timestamp field to `@timestamp`.
   - Click **Save**.

3. **Analyze Logs:**
   - Go to the **Discover** tab in the sidebar menu.
   - You will now see all logs enriched with Kubernetes metadata.
   - **Query Example:** Type `kubernetes.namespace_name: "prod-ecommerce"` to filter logs specific to your application, or `log: "ERROR"` to find application errors.

## Teardown
When you are finished learning:
```bash
kubectl delete namespace monitoring
```
