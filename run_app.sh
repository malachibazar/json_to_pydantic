#!/bin/bash

# Run the FastAPI app using uv
echo "Starting JSON to Pydantic converter app..."
uv run -m uvicorn main:app --reload

# This script won't reach here unless the app is stopped
echo "App stopped." 