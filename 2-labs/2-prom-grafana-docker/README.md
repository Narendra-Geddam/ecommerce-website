# Lab 2: Local Prometheus & Grafana (Docker Compose)

## Overview
This lab teaches you the fundamentals of metrics scraping and dashboard visualization without the complexity of Kubernetes. You will deploy Prometheus to scrape metrics from the Flask backend and Grafana to visualize them.

## Playground Requirements
- **Platform:** iximiuz Labs (https://labs.iximiuz.com/)
- **Playground Type:** `docker` or `ubuntu`
- **Why?** You need a pure Linux VM with the Docker engine running. 

## What to Install / Configure
Everything is handled by Docker Compose. 
Key configurations to study:
- `2-labs/2-prom-grafana-docker/prometheus-local.yml`: Look at the `scrape_configs` block. It defines how Prometheus continuously polls the `application:5000/metrics` endpoint to collect data.
- `2-labs/2-prom-grafana-docker/grafana-datasources-local.yml`: Notice how we automatically pre-configure Grafana to talk to the `http://prometheus:9090` endpoint, saving you from having to click through the UI to set up the data source.

## Execution Steps

1. Open your iximiuz `docker` playground terminal.
2. Clone this repository and enter it.
3. Start the lab using the orchestration script:
   ```bash
   ./2-labs/learning-lab.sh
   # Select option 3: Start App + Prometheus/Grafana
   ```
4. Verify the containers are running:
   ```bash
   docker ps
   ```

## Working and Analysis (How to use it)

1. **Expose Grafana:**
   - In the iximiuz UI, click **Expose Port**.
   - Enter port `3000`.
   - Click the generated URL to open the Grafana dashboard.
   - Login with **admin / admin**.

2. **Generate Traffic:**
   - In your iximiuz terminal, use `curl` to generate some test traffic against the application so Prometheus has data to scrape.
   ```bash
   curl http://localhost/api/products
   curl http://localhost/api/health
   ```

3. **Analyze Metrics in Grafana:**
   - Go to the **Explore** tab in Grafana (compass icon).
   - Ensure the data source dropdown is set to **Prometheus**.
   - In the metrics browser, enter a query like `flask_http_request_total` and hit **Run query**.
   - You should see graphs showing the requests you just generated!

## Teardown
When you are finished learning:
```bash
./2-labs/learning-lab.sh
# Select option 6: Teardown All Docker Compose Labs
```
