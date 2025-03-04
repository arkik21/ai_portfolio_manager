# documentation_generator

Documentation Generator Module

This module generates documentation from code comments and module docstrings.

**Module Path:** `documentation_generator`

## Table of Contents

### Classes

- [DocumentationGenerator](#documentationgenerator)

## Classes

### DocumentationGenerator

Generates project documentation from source code.

#### Methods

##### `__init__(source_dir, output_dir)`

Initialize the DocumentationGenerator.

Args:
    source_dir: Directory with source code
    output_dir: Directory to store generated documentation

**Type Hints:**

- **source_dir**: `str`
- **output_dir**: `str`

##### `generate_documentation()`

Generate documentation for all Python modules in the source directory.

##### `_find_python_files()`

Find all Python files in the source directory.

**Type Hints:**

- **returns**: `List[str]`

##### `_generate_file_documentation(file_path)`

Generate documentation for a Python file.

Args:
    file_path: Path to Python file

**Type Hints:**

- **file_path**: `str`

##### `_extract_class_info(node)`

Extract information about a class.

Args:
    node: AST node for the class
    
Returns:
    Dictionary with class information

**Type Hints:**

- **node**: `ast.ClassDef`
- **returns**: `Dict[str, Any]`

##### `_extract_function_info(node)`

Extract information about a function or method.

Args:
    node: AST node for the function
    
Returns:
    Dictionary with function information

**Type Hints:**

- **node**: `ast.FunctionDef`
- **returns**: `Dict[str, Any]`

##### `_get_name(node)`

Get name from an AST node.

**Type Hints:**

- **returns**: `str`

##### `_get_default_value(node)`

Get default value from an AST node.

**Type Hints:**

- **returns**: `str`

##### `_format_documentation(module_path, docstring, classes, functions)`

Format documentation content.

Args:
    module_path: Module import path
    docstring: Module docstring
    classes: List of class information
    functions: List of function information
    
Returns:
    Formatted documentation content

**Type Hints:**

- **module_path**: `str`
- **docstring**: `str`
- **classes**: `List[Dict[str, Any]]`
- **functions**: `List[Dict[str, Any]]`
- **returns**: `str`

##### `_format_class()`

Format class documentation.

Args:
    cls: Class information
    
Returns:
    Formatted class documentation

**Type Hints:**

- **cls**: `Dict[str, Any]`
- **returns**: `str`

##### `_format_method(method)`

Format method documentation.

Args:
    method: Method information
    
Returns:
    Formatted method documentation

**Type Hints:**

- **method**: `Dict[str, Any]`
- **returns**: `str`

##### `_format_function(func)`

Format function documentation.

Args:
    func: Function information
    
Returns:
    Formatted function documentation

**Type Hints:**

- **func**: `Dict[str, Any]`
- **returns**: `str`

##### `_generate_index()`

Generate index page with links to all documentation files.

##### `generate_html_documentation()`

Convert Markdown documentation to HTML.

##### `_convert_to_html(md_file)`

Convert Markdown file to HTML.

Args:
    md_file: Path to Markdown file

**Type Hints:**

- **md_file**: `str`

