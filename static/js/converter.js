/**
 * Detect if a string is a date or datetime.
 * Returns [is_date_or_time, type_string]
 */
function detectDateTime(value) {
    // Only allow specific date formats
    const datePatterns = [
        /^\d{4}-\d{2}-\d{2}$/, // YYYY-MM-DD
        /^\d{4}\/\d{2}\/\d{2}$/, // YYYY/MM/DD
    ];

    // Only allow specific datetime formats
    const datetimePatterns = [
        // ISO 8601 with T separator
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$/,
        // RFC3339 (subset of ISO 8601)
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/,
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}$/,
    ];

    // Check for date patterns
    for (const pattern of datePatterns) {
        if (pattern.test(value)) {
            const date = new Date(value);
            if (!isNaN(date.getTime())) {
                return [true, "date"];
            }
        }
    }

    // Check for datetime patterns
    for (const pattern of datetimePatterns) {
        if (pattern.test(value)) {
            const date = new Date(value);
            if (!isNaN(date.getTime())) {
                return [true, "datetime"];
            }
        }
    }

    return [false, "str"];
}

/**
 * Determine the Python type based on a JSON value
 */
function getPythonType(value) {
    if (value === null) {
        return "None";
    } else if (typeof value === "boolean") {
        return "bool";
    } else if (Number.isInteger(value)) {
        return "int";
    } else if (typeof value === "number") {
        return "float";
    } else if (typeof value === "string") {
        const [isDateTime, dateType] = detectDateTime(value);
        if (isDateTime) {
            return dateType;
        }
        return "str";
    } else if (Array.isArray(value)) {
        if (value.length === 0) {
            return "list[Any]";
        }
        const types = new Set(value.map(item => getPythonType(item)));
        if (types.size === 1) {
            return `list[${types.values().next().value}]`;
        } else {
            return "list[Any]";
        }
    } else if (typeof value === "object") {
        return "dict[str, Any]";
    } else {
        return "Any";
    }
}

/**
 * Convert snake_case or camelCase to PascalCase
 */
function toPascalCase(snakeStr) {
    if (!snakeStr) {
        return "MyModel";
    }
    
    let words;
    if (snakeStr.includes("_") || snakeStr.includes("-") || snakeStr.includes(" ")) {
        words = snakeStr.split(/[_\- ]/);
    } else {
        // Handle camelCase
        const s1 = snakeStr.replace(/(.)([A-Z][a-z]+)/g, "$1 $2");
        const s2 = s1.replace(/([a-z0-9])([A-Z])/g, "$1 $2");
        words = s2.split(" ");
    }

    return words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join("");
}

/**
 * Convert camelCase to snake_case
 */
function camelToSnake(name) {
    let result = name.replace(/(.)([A-Z][a-z]+)/g, "$1_$2");
    result = result.replace(/([a-z0-9])([A-Z])/g, "$1_$2");
    return result.toLowerCase();
}

/**
 * Check if a string is camelCase
 */
function isCamelCase(text) {
    if (!text) return false;
    // Must start with lowercase and contain at least one uppercase
    // And no underscores, spaces, or hyphens
    return (
        /^[a-z]/.test(text) &&
        /[A-Z]/.test(text) &&
        !text.includes("_") &&
        !text.includes(" ") &&
        !text.includes("-")
    );
}

/**
 * Generate a Pydantic model string from a JSON object
 */
function generatePydanticModel(jsonData, modelName = "MyModel", _nestedModels = null, makeOptional = false, convertCamelCase = false) {
    if (_nestedModels === null) {
        _nestedModels = [];
    }

    const typesUsed = new Set();
    const modelLines = [`class ${modelName}(BaseModel):`];

    if (!jsonData || Object.keys(jsonData).length === 0) {
        modelLines.push("    pass");
    } else {
        for (const [key, value] of Object.entries(jsonData)) {
            let fieldName = key;
            let snakeName = null;

            if (convertCamelCase && isCamelCase(key)) {
                snakeName = camelToSnake(key);
                fieldName = snakeName;
            }

            let fieldType;
            if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
                const nestedName = toPascalCase(fieldName);
                _nestedModels.push([nestedName, value]);
                fieldType = nestedName;
            } else if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'object' && value[0] !== null) {
                let nestedName = toPascalCase(fieldName);
                if (nestedName.endsWith("s")) {
                    nestedName = nestedName.slice(0, -1);
                }
                _nestedModels.push([nestedName, value[0]]);
                fieldType = `list[${nestedName}]`;
            } else {
                fieldType = getPythonType(value);
                if (["date", "datetime"].includes(fieldType)) {
                    typesUsed.add(fieldType);
                }
            }

            if (makeOptional) {
                fieldType = `${fieldType} | None = None`;
            }

            if (snakeName && key !== snakeName) {
                modelLines.push(`    ${fieldName}: ${fieldType} = Field(alias='${key}')`);
            } else {
                modelLines.push(`    ${fieldName}: ${fieldType}`);
            }
        }

        if (convertCamelCase) {
            modelLines.push("");
            modelLines.push("    model_config = ConfigDict(populate_by_name=True)");
        }
    }

    // Top-level call processing
    if (modelName === "MyModel" && !_nestedModels.slice(0, -1).some(([name]) => name === "MyModel")) {
        const outputLines = [
            "from pydantic import BaseModel, Field, ConfigDict",
            "from typing import Any",
        ];

        const allTypesUsed = new Set(typesUsed);
        const processedModels = new Set();
        const remainingModels = [..._nestedModels];
        const nestedModelCode = [];

        while (remainingModels.length > 0) {
            const [name, data] = remainingModels.shift();
            if (!processedModels.has(name)) {
                const nestedTypesUsed = new Set();
                const nestedModelLines = [`class ${name}(BaseModel):`];

                for (const [k, v] of Object.entries(data)) {
                    let currentKey = k;
                    const origKey = k;
                    
                    if (convertCamelCase && isCamelCase(k)) {
                        currentKey = camelToSnake(k);
                    }

                    let fieldType;
                    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
                        const nestedName = toPascalCase(currentKey);
                        remainingModels.push([nestedName, v]);
                        fieldType = nestedName;
                    } else if (Array.isArray(v) && v.length > 0 && typeof v[0] === 'object' && v[0] !== null) {
                        let nestedName = toPascalCase(currentKey);
                        if (nestedName.endsWith("s")) {
                            nestedName = nestedName.slice(0, -1);
                        }
                        remainingModels.push([nestedName, v[0]]);
                        fieldType = `list[${nestedName}]`;
                    } else {
                        fieldType = getPythonType(v);
                        if (["date", "datetime"].includes(fieldType)) {
                            nestedTypesUsed.add(fieldType);
                        }
                    }

                    if (makeOptional) {
                        fieldType = `${fieldType} | None = None`;
                    }

                    if (convertCamelCase && isCamelCase(origKey) && currentKey !== origKey) {
                        nestedModelLines.push(`    ${currentKey}: ${fieldType} = Field(alias='${origKey}')`);
                    } else {
                        nestedModelLines.push(`    ${currentKey}: ${fieldType}`);
                    }
                }

                if (convertCamelCase) {
                    nestedModelLines.push("");
                    nestedModelLines.push("    model_config = ConfigDict(populate_by_name=True)");
                }

                nestedModelCode.push(nestedModelLines.join("\n"));
                nestedModelCode.push("");
                processedModels.add(name);
                nestedTypesUsed.forEach(t => allTypesUsed.add(t));
            }
        }

        if (allTypesUsed.has("date") && !allTypesUsed.has("datetime")) {
            outputLines.push("from datetime import date");
        } else if (allTypesUsed.has("datetime") && !allTypesUsed.has("date")) {
            outputLines.push("from datetime import datetime");
        } else if (allTypesUsed.has("date") && allTypesUsed.has("datetime")) {
            outputLines.push("from datetime import date, datetime");
        }

        outputLines.push("");
        outputLines.push("");

        outputLines.push(...nestedModelCode);
        outputLines.push(...modelLines);

        return outputLines.join("\n");
    } else {
        return modelLines.join("\n");
    }
}
