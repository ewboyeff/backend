#!/bin/sh
set -e

echo "=== Charity Index Backend Starting ==="

echo "Waiting for database to be ready..."
python - << 'EOF'
import time
import os
import sys
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL", "")
if not db_url:
    print("DATABASE_URL not set, skipping wait.")
    sys.exit(0)

print(f"Connecting to database...")
max_retries = 30
for i in range(max_retries):
    try:
        import socket
        # Parse host and port from DATABASE_URL
        clean_url = db_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://")
        parsed = urlparse(clean_url)
        host = parsed.hostname or "postgres"
        port = parsed.port or 5432
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"Database port {port} on {host} is reachable!")
            sys.exit(0)
    except Exception as e:
        pass
    print(f"Waiting for database... ({i+1}/{max_retries})")
    time.sleep(2)

print("Warning: Timed out waiting for database, proceeding anyway...")
EOF

echo "Applying Alembic migrations..."
alembic upgrade head

echo "Seeding initial database data..."
python scripts/seed.py || true

echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
