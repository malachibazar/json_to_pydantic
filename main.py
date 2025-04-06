from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
from typing import Any, Optional, Tuple
import re
from datetime import datetime

app = FastAPI(
    title="JSON to Pydantic Converter",
    description="Convert JSON data to Pydantic models",
)

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Static directory might not exist yet
    pass


# SEO-friendly routes
@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt():
    """Serve robots.txt file for search engines"""
    robots_path = os.path.join("static", "robots.txt")
    if os.path.exists(robots_path):
        with open(robots_path, "r") as f:
            return f.read()
    return "User-agent: *\nAllow: /\n"


@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def get_sitemap():
    """Serve sitemap.xml file for search engines"""
    sitemap_path = os.path.join("static", "sitemap.xml")
    if os.path.exists(sitemap_path):
        with open(sitemap_path, "r") as f:
            content = f.read()
        return PlainTextResponse(content=content, media_type="application/xml")

    # Generate simple sitemap if file doesn't exist
    return PlainTextResponse(
        content=(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            "  <url>\n"
            "    <loc>https://json-to-pydantic.malachibazar.com/</loc>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>1.0</priority>\n"
            "  </url>\n"
            "</urlset>"
        ),
        media_type="application/xml",
    )


def detect_date_time(value: str) -> Tuple[bool, str]:
    """
    Detect if a string is a date or datetime.
    Returns (is_date_or_time, type_string)

    Supports a limited set of strict formats:
    - Dates: YYYY-MM-DD, YYYY/MM/DD
    - Datetimes: ISO 8601 with T separator and optional timezone
    """
    # Only allow specific date formats
    date_patterns = [
        # ISO 8601
        r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
        r"^\d{4}/\d{2}/\d{2}$",  # YYYY/MM/DD
    ]

    # Only allow specific datetime formats - more strict than before
    datetime_patterns = [
        # ISO 8601 with T separator
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$",  # ISO with T
        # RFC3339 (subset of ISO 8601)
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$",  # UTC with Z
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}$",  # With timezone offset
    ]

    # Try to parse with actual datetime parsing to validate
    try:
        # Check for date patterns
        for pattern in date_patterns:
            if re.match(pattern, value):
                # Validate by trying to parse
                try:
                    if "-" in value:
                        datetime.strptime(value, "%Y-%m-%d")
                    elif "/" in value:
                        datetime.strptime(value, "%Y/%m/%d")
                    else:
                        continue
                    return True, "date"
                except ValueError:
                    # If parsing fails, it's not a valid date
                    continue

        # Check for datetime patterns
        for pattern in datetime_patterns:
            if re.match(pattern, value):
                # Try to parse with ISO format
                try:
                    # For ISO format with T
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                    return True, "datetime"
                except ValueError:
                    # If parsing fails, it's not a valid datetime
                    continue

    except (ValueError, TypeError):
        pass

    return False, "str"


def get_python_type(value: Any) -> str:
    """Determine the Python type based on a JSON value"""
    if value is None:
        return "None"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        # Check if this string looks like a date or datetime
        is_date_time, date_type = detect_date_time(value)
        if is_date_time:
            return date_type
        return "str"
    elif isinstance(value, list):
        if not value:
            return "list[Any]"
        types = set(get_python_type(item) for item in value)
        if len(types) == 1:
            return f"list[{next(iter(types))}]"
        else:
            return "list[Any]"
    elif isinstance(value, dict):
        return "dict[str, Any]"
    else:
        return "Any"


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case or camelCase to PascalCase"""
    if not snake_str:
        return "MyModel"
    # Handle snake_case, kebab-case, or space delimited
    if "_" in snake_str or "-" in snake_str or " " in snake_str:
        words = re.split(r"[_\- ]", snake_str)
    else:
        # Handle camelCase by finding capital letters
        # Add space before capital letters to split
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1 \2", snake_str)
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1 \2", s1)
        words = s2.split()

    return "".join(word.capitalize() for word in words)


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def is_camel_case(text: str) -> bool:
    """Check if a string is camelCase"""
    if not text:
        return False
    # Must start with lowercase and contain at least one uppercase
    return (
        text[0].islower()
        and any(c.isupper() for c in text)
        and "_" not in text
        and " " not in text
        and "-" not in text
    )


def generate_pydantic_model(
    json_data: dict[str, Any],
    model_name: str = "MyModel",
    _nested_models: list = None,
    make_optional: bool = False,
    convert_camel_case: bool = False,
) -> str:
    """Generate a Pydantic model string from a JSON object"""
    if _nested_models is None:
        _nested_models = []

    # Track the types used in this model
    types_used = set()
    model_lines = [f"class {model_name}(BaseModel):"]

    if not json_data:
        model_lines.append("    pass")
    else:
        # Process each field
        for key, value in json_data.items():
            field_name = key

            # Handle camelCase conversion if enabled
            snake_name = None
            if convert_camel_case and is_camel_case(key):
                snake_name = camel_to_snake(key)
                field_name = snake_name

            if isinstance(value, dict):
                # Create a nested model for dict values
                nested_name = to_pascal_case(field_name)
                # Add to nested models for later processing
                _nested_models.append((nested_name, value))
                field_type = nested_name
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Create a nested model for list of dicts
                nested_name = to_pascal_case(field_name)
                if nested_name.endswith("s"):
                    nested_name = nested_name[:-1]  # Remove plural 's'
                # Add to nested models for later processing
                _nested_models.append((nested_name, value[0]))
                field_type = f"list[{nested_name}]"
            else:
                field_type = get_python_type(value)
                # Track special types for imports
                if field_type in ["date", "datetime"]:
                    types_used.add(field_type)

            # Handle optional fields if enabled
            if make_optional:
                field_type = f"{field_type} | None = None"

            # Add field alias if camelCase conversion is enabled
            if snake_name and key != snake_name:
                field_line = f"    {field_name}: {field_type} = Field(alias='{key}')"
            else:
                field_line = f"    {field_name}: {field_type}"

            model_lines.append(field_line)

        # If using camelCase, we need model_config
        if convert_camel_case:
            model_lines.append("")
            model_lines.append("    model_config = ConfigDict(populate_by_name=True)")

    # If this is the top-level call, process all nested models and assemble the full output
    if model_name == "MyModel" and not any(
        name == "MyModel" for name, _ in _nested_models[:-1] if _nested_models
    ):
        # Start with imports
        output_lines = [
            "from pydantic import BaseModel, Field, ConfigDict",
            "from typing import Any",
        ]

        # Add date/datetime imports if needed
        all_types_used = types_used.copy()

        # Process all nested models first (to collect their type usage)
        processed_models = set()
        remaining_models = _nested_models.copy()

        # Placeholder for nested model lines to be processed later
        nested_model_code = []

        # First process all nested models to gather type information
        while remaining_models:
            name, data = remaining_models.pop(0)
            if name not in processed_models:
                # Temp collection for types used in this nested model
                nested_types_used = set()

                # Generate this model's lines with the same options
                nested_model_lines = [f"class {name}(BaseModel):"]
                for k, v in data.items():
                    # Apply the same options to nested models
                    orig_key = k
                    if convert_camel_case and is_camel_case(k):
                        k = camel_to_snake(k)

                    if isinstance(v, dict):
                        nested_name = to_pascal_case(k)
                        remaining_models.append((nested_name, v))
                        field_type = nested_name
                    elif isinstance(v, list) and v and isinstance(v[0], dict):
                        nested_name = to_pascal_case(k)
                        if nested_name.endswith("s"):
                            nested_name = nested_name[:-1]
                        remaining_models.append((nested_name, v[0]))
                        field_type = f"list[{nested_name}]"
                    else:
                        field_type = get_python_type(v)
                        # Track special types
                        if field_type in ["date", "datetime"]:
                            nested_types_used.add(field_type)

                    # Apply optional type if enabled
                    if make_optional:
                        field_type = f"{field_type} | None = None"

                    # Add field alias if camelCase conversion is enabled
                    if convert_camel_case and is_camel_case(orig_key) and k != orig_key:
                        nested_model_lines.append(
                            f"    {k}: {field_type} = Field(alias='{orig_key}')"
                        )
                    else:
                        nested_model_lines.append(f"    {k}: {field_type}")

                # Add model_config if needed
                if convert_camel_case:
                    nested_model_lines.append("")
                    nested_model_lines.append(
                        "    model_config = ConfigDict(populate_by_name=True)"
                    )

                nested_model_code.append("\n".join(nested_model_lines))
                nested_model_code.append("")  # Empty line after each model for spacing
                processed_models.add(name)
                all_types_used.update(nested_types_used)

        # Add imports for date/datetime if needed
        if "date" in all_types_used and "datetime" not in all_types_used:
            output_lines.append("from datetime import date")
        elif "datetime" in all_types_used and "date" not in all_types_used:
            output_lines.append("from datetime import datetime")
        elif "date" in all_types_used and "datetime" in all_types_used:
            output_lines.append("from datetime import date, datetime")

        # Add blank lines after imports
        output_lines.append("")
        output_lines.append("")

        # Add nested models and main model
        output_lines.extend(nested_model_code)
        output_lines.extend(model_lines)

        return "\n".join(output_lines)
    else:
        # If not the top-level call, just return the model lines
        return "\n".join(model_lines)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "pydantic_model": "",
            "json_input": "",
            "make_optional": False,
            "convert_camel_case": False,
        },
    )


@app.post("/", response_class=HTMLResponse)
async def convert_json(
    request: Request,
    json_input: str = Form(...),
    make_optional: bool = Form(False),
    convert_camel_case: bool = Form(False),
):
    try:
        if not json_input.strip():
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "pydantic_model": "",
                    "json_input": "",
                    "make_optional": make_optional,
                    "convert_camel_case": convert_camel_case,
                    "error": "Please enter some JSON",
                },
            )

        json_data = json.loads(json_input)
        if not isinstance(json_data, dict):
            raise ValueError("Input JSON must be an object/dictionary")

        pydantic_model = generate_pydantic_model(
            json_data,
            make_optional=make_optional,
            convert_camel_case=convert_camel_case,
        )

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "pydantic_model": pydantic_model,
                "json_input": json_input,
                "make_optional": make_optional,
                "convert_camel_case": convert_camel_case,
            },
        )
    except json.JSONDecodeError:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "pydantic_model": "",
                "json_input": json_input,
                "make_optional": make_optional,
                "convert_camel_case": convert_camel_case,
                "error": "Invalid JSON format",
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "pydantic_model": "",
                "json_input": json_input,
                "make_optional": make_optional,
                "convert_camel_case": convert_camel_case,
                "error": str(e),
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
