#!/bin/bash

# Deploy the application (replace with your actual deployment commands)
echo "Deploying JSON to Pydantic Converter..."

# Restart your application
sudo systemctl restart json_to_pydantic

# Wait for the application to start
echo "Waiting for application to start..."
sleep 10

# Your domain
DOMAIN="https://jsontopydantic.dev"

# Notify search engines about your sitemap
echo "Notifying search engines about sitemap..."

# Google
echo "Pinging Google..."
curl "https://www.google.com/ping?sitemap=${DOMAIN}/sitemap.xml"

# Bing
echo "Pinging Bing..."
curl "https://www.bing.com/ping?sitemap=${DOMAIN}/sitemap.xml"

echo "Deployment and search engine notification complete!" 