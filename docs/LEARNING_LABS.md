# Observability Learning Labs

This repository is designed as a "production simulator" to help you learn cloud-native concepts and observability tools in a structured way.

We have structured the labs specifically for **[iximiuz Labs](https://labs.iximiuz.com)**, meaning you have a fully functional Linux/Kubernetes environment without any local setup headaches.

## 🗺️ Recommended Learning Roadmap

If you are new to observability, we strongly recommend following the labs in this specific order to build your understanding from the ground up:

1. **Start with Lab 1 (`2-labs/1-elk-docker`):** Learn the absolute basics of how a log shipper (Fluent Bit) reads raw text files from the Docker daemon (`/var/lib/docker/containers`) and sends them to a database.
2. **Move to Lab 2 (`2-labs/2-prom-grafana-docker`):** Learn how metrics fundamentally differ from logs. See how Prometheus "pulls" (scrapes) data from your Flask app's `/metrics` endpoint.
3. **Advance to Lab 3 (`2-labs/3-plg-k8s`):** Now introduce Kubernetes. See how `Promtail` runs as a DaemonSet to achieve the exact same thing you did in Lab 1, but dynamically across a cluster using Loki.
4. **Master Lab 4 (`2-labs/4-efk-k8s`):** Graduate to the enterprise standard. See how Fluent Bit enriches raw logs with Kubernetes metadata (like namespaces and pod names) so you can do advanced querying in Kibana.

## Available Labs

You can orchestrate these labs using the central setup script:

```bash
chmod +x 2-labs/learning-lab.sh
./2-labs/learning-lab.sh
```

### Lab 1: ELK Stack via Docker Compose
**Goal:** Learn how log aggregation works at the container level before moving to Kubernetes.
- Runs `elasticsearch`, `kibana`, and `fluent-bit`.
- Fluent Bit directly mounts the iximiuz node's `/var/lib/docker/containers` to harvest logs.
- **Port:** Kibana is on `5601`.

### Lab 2: Prometheus & Grafana via Docker Compose
**Goal:** Learn metrics scraping and dashboard creation.
- Runs `prometheus` and `grafana`.
- Prometheus scrapes the local Flask application.
- **Port:** Grafana is on `3000`.

### Lab 3: PLG Stack via Kubernetes
**Goal:** Learn the modern, lightweight Kubernetes log aggregation stack.
- Deploys Loki (storage) and Promtail (DaemonSet shipper).
- **Port:** Grafana is on `3000`.

### Lab 4: EFK Stack via Kubernetes
**Goal:** Learn the enterprise-standard Kubernetes log aggregation stack.
- Deploys Elasticsearch (storage) and Fluent Bit (DaemonSet shipper).
- **Port:** Kibana is on `5601`.

## How to Access Dashboards in iximiuz

Since you are running inside an iximiuz Labs browser playground, you cannot simply browse to `localhost`. You must expose the port using the iximiuz UI:

1. **Ensure the port is bound to `0.0.0.0`:**
   - Docker Compose does this automatically (e.g., `ports: - "5601:5601"`).
   - For Kubernetes, our deploy script automatically adds the `--address 0.0.0.0` flag to `kubectl port-forward`.
2. **Expose the Port:**
   - In the top right corner of the iximiuz playground, click **"Expose Port"**.
   - Select your VM, enter the port number (e.g., `5601` or `3000`), and click Expose.
   - Click the generated URL to access your dashboard!
