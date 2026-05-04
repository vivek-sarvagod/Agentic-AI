#!/bin/sh
# entrypoint.sh — Runtime environment variable injection for the React/Vite SPA.
#
# Vite bakes VITE_* env vars into the JS bundle at build time.
# The image is built with the placeholder "http://RUNTIME_API_URL_PLACEHOLDER".
# At container start this script replaces that placeholder with the value of
# the VITE_API_BASE_URL environment variable supplied by Kubernetes (via ConfigMap).
#
# This allows a single Docker image to be deployed to multiple environments
# (dev / staging / prod) without rebuilding.

set -e

PLACEHOLDER="http://RUNTIME_API_URL_PLACEHOLDER"
API_URL="${VITE_API_BASE_URL:-}"

echo "[entrypoint] VITE_API_BASE_URL = '${API_URL}'"

if [ -d "/usr/share/nginx/html" ]; then
    find /usr/share/nginx/html -name "*.js" -type f | while IFS= read -r file; do
        if grep -q "${PLACEHOLDER}" "${file}" 2>/dev/null; then
            sed -i "s|${PLACEHOLDER}|${API_URL}|g" "${file}"
            echo "[entrypoint] Patched: ${file}"
        fi
    done
fi

echo "[entrypoint] Starting nginx..."
exec nginx -g "daemon off;"
