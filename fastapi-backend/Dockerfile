FROM ghcr.io/prefix-dev/pixi:0.39.2 AS build

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

# Run the application
# We use `pixi run` to ensure we use the environment we just installed
CMD ["pixi", "run", "start"]
