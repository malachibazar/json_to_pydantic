# JSON to Pydantic Converter

A web application that converts JSON data into Pydantic model definitions.

## Features

- **Interactive Web Interface**
  - Clean, two-panel layout with syntax highlighting
  - JSON input on the left, Pydantic model on the right
  - Copy-to-clipboard functionality
  - Sample JSON data for quick testing

- **Smart Type Detection**
  - Automatic detection of standard Python types (str, int, bool, etc.)
  - **Date and datetime detection** with appropriate imports
  - Handles nested objects and lists
  - Properly generates type annotations for complex structures

- **Advanced Customization Options**
  - **Optional fields**: Make all fields optional with `None` defaults
  - **CamelCase conversion**: Convert camelCase JSON keys to snake_case with field aliases
  - Modern Pydantic v2 compatible output using `model_config = ConfigDict()`

- **Nested Model Generation**
  - Automatically creates nested models for complex JSON structures
  - Proper naming of nested classes (e.g., singular form for list item types)
  - Maintains type hierarchies for deeply nested objects

## Requirements

- Python 3.11+
- FastAPI
- uv (modern Python package manager)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/malachibazar/json_to_pydantic.git
cd json_to_pydantic
```

1. Install dependencies with uv:

```bash
# Create a virtual environment and install dependencies in one step
uv sync
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

1. Paste your JSON data into the left panel (or use "Load Sample JSON")
2. Select generation options:
   - Check "Make all fields optional" to make all fields optional with None defaults
   - Check "Convert camelCase to snake_case with aliases" to use snake_case field names
3. Click "Generate Pydantic Model"
4. The equivalent Pydantic model will appear in the right panel
5. Click "Copy to Clipboard" to copy the generated model

## How It Works

The application uses Python's type system and a recursive algorithm to analyze JSON structures and generate appropriate Pydantic model classes:

1. Parses the JSON input and validates its structure
2. Identifies field types through intelligent type detection, including dates
3. Recursively processes nested objects to create appropriate model classes
4. Applies requested customizations (optional fields, camelCase conversion)
5. Generates properly formatted Pydantic models with correct imports
6. Returns the model code that can be used directly in Python applications

## Examples

### Simple JSON

```json
{
  "name": "John Doe",
  "age": 30,
  "email": "john@example.com",
  "is_active": true
}
```

Generates:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Any


class MyModel(BaseModel):
    name: str
    age: int
    email: str
    is_active: bool
```

### With Date/Time Detection

```json
{
  "user_id": 1234,
  "username": "johndoe",
  "created_date": "2023-01-01",
  "last_login": "2023-01-15T14:30:45Z"
}
```

Generates:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from datetime import date, datetime


class MyModel(BaseModel):
    user_id: int
    username: str
    created_date: date
    last_login: datetime
```

## License

MIT
