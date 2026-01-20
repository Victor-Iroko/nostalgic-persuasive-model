FROM ghcr.io/prefix-dev/pixi:0.39.2 AS build

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy pixi configuration
COPY pixi.toml pixi.lock ./

# Install dependencies matching the lock file
RUN pixi install --frozen

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Create bandit_models directory for persistent bandit data
RUN mkdir -p bandit_models && chown -R appuser:appgroup bandit_models

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Set ownership of app directory
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Run the application
# We use `pixi run` to ensure we use the environment we just installed
CMD ["pixi", "run", "start"]
