#!/bin/sh
set -e

SCRAPYD_URL="http://localhost:6800"


cd /app

echo "[entrypoint] Starting Scrapyd in the background..."
scrapyd &
SCRAPYD_PID=$!

echo "[entrypoint] Waiting for Scrapyd to become ready at ${SCRAPYD_URL} ..."
until curl -sf "${SCRAPYD_URL}/daemonstatus.json" >/dev/null 2>&1; do
   
    if ! kill -0 "${SCRAPYD_PID}" 2>/dev/null; then
        echo "[entrypoint] ERROR: Scrapyd exited before becoming ready." >&2
        exit 1
    fi
    sleep 1
done
echo "[entrypoint] Scrapyd is ready."


echo "[entrypoint] Deploying project 'books_scraper' to target 'local'..."
cd /app/books_scraper
scrapyd-deploy local -p books_scraper
cd /app

echo "[entrypoint] Deployment complete. Spider is now schedulable via the Scrapyd API."
echo "[entrypoint] Keeping Scrapyd in the foreground; container will stay alive."


wait "${SCRAPYD_PID}"
