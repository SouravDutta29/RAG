#!/bin/sh

echo "Waiting for API to be ready..."
# The healthcheck already ensures the API is healthy, but we can double check
sleep 2

echo "Triggering ingestion process..."
response=$(curl -s -X POST http://api:8000/api/v1/ingest)
echo "Ingest Response: $response"

echo "Ingestion job finished."
