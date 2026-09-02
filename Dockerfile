# Bayesian Poker Agent - web UI container image
#
# Build:  docker build -t bayesian-poker-agent .
# Run:    docker run -p 5000:5000 -e FLASK_SECRET_KEY=$(openssl rand -hex 32) bayesian-poker-agent
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Set FLASK_SECRET_KEY at deploy time (e.g. `docker run -e FLASK_SECRET_KEY=...`)
# so player sessions survive container restarts. Flask's dev server is fine
# for a portfolio/demo deployment; swap in gunicorn for real production traffic.
CMD ["python", "app.py"]
