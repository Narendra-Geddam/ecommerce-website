# Lab 1: Local ELK Stack (Docker Compose)

## Overview
This lab teaches you how log aggregation works at a raw container level without Kubernetes. You will deploy Elasticsearch, Kibana, and a Fluent Bit log shipper. Fluent Bit will mount the host's `/var/lib/docker/containers` directory to scrape logs directly from the Docker daemon and send them to Elasticsearch.

## Playground Requirements
- **Platform:** iximiuz Labs (https://labs.iximiuz.com/)
- **Playground Type:** `docker` or `ubuntu`
- **Why?** You need a pure Linux VM with the Docker engine running. The K3s playgrounds also work, but a pure Docker playground is simpler for this specific lab.

## What to Install / Configure
Nothing needs to be manually installed! Everything is handled by Docker Compose. 
However, you should review the configuration files to understand how it works:
- `2-labs/1-elk-docker/fluent-bit-local.conf`: Look at how the `[INPUT]` section tails the `/var/lib/docker/containers/*/*.log` paths.
- `2-labs/1-elk-docker/docker-compose-elk.yml`: Notice how the `/var/lib/docker/containers` volume is mounted as read-only (`:ro`) into the `fluent-bit` container.

## Execution Steps

1. Open your iximiuz `docker` playground terminal.
2. Clone this repository and enter it.
3. Start the lab using the orchestration script:
   ```bash
   ./scripts/setup/learning-lab.sh
   # Select option 2: Start App + ELK Stack
   ```
4. Verify the containers are running:
   ```bash
   docker ps
   ```
   *You should see the frontend, backend, database, elasticsearch, kibana, and fluent-bit containers.*

## Working and Analysis (How to use it)

1. **Expose Kibana:**
   - In the iximiuz UI, click **Expose Port**.
   - Enter port `5601`.
   - Click the generated URL to open the Kibana dashboard.

2. **Configure Index Pattern:**
   - In Kibana, click the hamburger menu (top left) -> **Stack Management** -> **Data Views** (or Index Patterns).
   - Click **Create Data View**.
   - Name it `fluent-bit-*` and set the timestamp field to `@timestamp` or `time`.
   - Click **Save**.

3. **Analyze Logs:**
   - Go to the **Discover** tab in the sidebar menu.
   - You will now see all logs from your Flask backend, Nginx frontend, and Postgres database.
   - **Query Example:** Type `kubernetes.labels.app: "ecommerce-backend"` or `flask` in the search bar to filter logs specific to your backend API.

## Teardown
When you are finished learning:
```bash
./scripts/setup/learning-lab.sh
# Select option 6: Teardown All Docker Compose Labs
```
