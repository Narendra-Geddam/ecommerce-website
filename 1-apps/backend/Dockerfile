# Application Tier - Flask Backend API
# Use a newer Python base and apply OS upgrades to reduce known CVEs
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install curl for health checks and apply security updates
RUN apt-get update \
	&& apt-get upgrade -y \
	&& apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py observability.py ./

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "app:app"]
