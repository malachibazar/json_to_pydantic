# JSON to Pydantic Converter

A web application that converts JSON data into Pydantic model definitions.

## Features

- Simple web interface with a two-panel layout
- JSON input validation
- Automatic type detection
- Nested model generation for complex JSON structures
- Copy-to-clipboard functionality
- Sample JSON data for testing

## Requirements

- Python 3.13+
- FastAPI
- uv (modern Python package manager)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd json-to-pydantic
```

2. Install dependencies with uv:
```bash
# Create a virtual environment and install dependencies in one step
uv pip install -e .
```

## Running the Application

Start the application with uv (handles virtual environment automatically):

```bash
uv run -m uvicorn main:app --reload
```

Or use the provided script:

```bash
./run_app.sh
```

Then open your browser and navigate to: [http://localhost:8000](http://localhost:8000)

## Running Tests

Run the tests using:

```bash
uv run test_app.py
```

Or use the provided script:

```bash
./run_tests.sh
```

## Usage

1. Paste your JSON data into the left panel
2. Click "Generate Pydantic Model"
3. The equivalent Pydantic model will appear in the right panel
4. Click "Copy to Clipboard" to copy the generated model

You can also click "Load Sample JSON" to try out the application with predefined JSON data.

## How It Works

The application uses Python's type system and a recursive algorithm to traverse JSON structures and generate appropriate Pydantic model classes. It handles nested objects, arrays, and various data types.

## License

MIT
