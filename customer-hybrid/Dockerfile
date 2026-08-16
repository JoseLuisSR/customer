# Use the lightweight Python 3.12 image based on Alpine Linux
FROM python:3.14-alpine

# Copy the uv and uvx executables from the official uv image
COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /uvx /bin/

# Set /app as the working directory inside the container
WORKDIR /app

# Copy all application files into the working directory
COPY . .

# Install locked production dependencies without using the package cache
RUN uv sync --locked --no-dev --no-cache

# Document that the application listens on port 8000
EXPOSE 8000

# Start the Flask application using Gunicorn
CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "main:app"]