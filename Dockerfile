# Stage 1: Build frontend
FROM oven/bun:1 AS frontend-builder

WORKDIR /app/ui
COPY ui/package.json ui/bun.lockb* ./
RUN bun install --frozen-lockfile

COPY ui/ ./
RUN bun run build

# Stage 2: Python app
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_server.py config.py ner_extractor.py pro_ctcae_mapper.py session_manager.py ./
COPY process_existing_files.py ./

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/ui/../static ./static

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
	CMD curl -f http://localhost:8000/api/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:8000", "--timeout", "120", "api_server:create_app()"]
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "120", "api_server:create_app()"]
