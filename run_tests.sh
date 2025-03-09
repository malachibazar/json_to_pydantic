#!/bin/bash

# Run the tests using uv - no need for manual venv activation
echo "Running tests with uv..."
uv run test_app.py

echo "Tests complete!" 