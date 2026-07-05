# Use an official Python slim image
FROM python:3.10-slim

# Copy the uv binary from the official astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy dependency definition files first (for Docker caching)
COPY pyproject.toml uv.lock ./

# Install dependencies without the project itself and without dev dependencies
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the project files
COPY . .

# Final sync to install the project
RUN uv sync --frozen --no-dev

# Expose the port Uvicorn will listen on
EXPOSE 8000

# Start the FastAPI application via Uvicorn
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
