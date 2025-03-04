"""
Documentation Generator Module

This module generates documentation from code comments and module docstrings.
"""

import os
import re
import ast
import inspect
import importlib
import logging
from typing import Dict, List, Any, Optional, Tuple
import yaml
import markdown

# Import custom utility module
from utility.logging_utility import get_logger

logger = get_logger('documentation')

class DocumentationGenerator:
    """Generates project documentation from source code."""
    
    def __init__(self, source_dir: str, output_dir: str):
        """
        Initialize the DocumentationGenerator.
        
        Args:
            source_dir: Directory with source code
            output_dir: Directory to store generated documentation
        """
        self.source_dir = source_dir
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_documentation(self):
        """Generate documentation for all Python modules in the source directory."""
        logger.info(f"Generating documentation from {self.source_dir}")
        
        # Find all Python files
        python_files = self._find_python_files()
        logger.info(f"Found {len(python_files)} Python files")
        
        # Generate documentation for each file
        for file_path in python_files:
            self._generate_file_documentation(file_path)
        
        # Generate index file
        self._generate_index()
        
        logger.info(f"Documentation generated in {self.output_dir}")
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the source directory."""
        python_files = []
        
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        
        return python_files
    
    def _generate_file_documentation(self, file_path: str):
        """
        Generate documentation for a Python file.
        
        Args:
            file_path: Path to Python file
        """
        # Get relative path for output file
        rel_path = os.path.relpath(file_path, self.source_dir)
        module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
        
        # Skip __init__.py files in documentation
        if module_path.endswith('__init__'):
            return
        
        logger.debug(f"Generating documentation for {module_path}")
        
        # Parse file
        with open(file_path, 'r') as f:
            file_content = f.read()
        
        # Extract docstring and code structure
        try:
            module = ast.parse(file_content)
            docstring = ast.get_docstring(module)
            
            # Extract classes and functions
            classes = []
            functions = []
            
            for node in module.body:
                if isinstance(node, ast.ClassDef):
                    classes.append(self._extract_class_info(node))
                elif isinstance(node, ast.FunctionDef):
                    functions.append(self._extract_function_info(node))
            
            # Generate documentation content
            doc_content = self._format_documentation(
                module_path, docstring, classes, functions)
            
            # Save documentation
            output_path = os.path.join(
                self.output_dir, 
                os.path.dirname(rel_path),
                f"{os.path.basename(rel_path).replace('.py', '.md')}"
            )
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(doc_content)
                
            logger.debug(f"Documentation saved to {output_path}")
            
        except SyntaxError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
    
    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """
        Extract information about a class.
        
        Args:
            node: AST node for the class
            
        Returns:
            Dictionary with class information
        """
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'methods': []
        }
        
        # Add base classes
        class_info['bases'] = [self._get_name(base) for base in node.bases]
        
        # Extract methods
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                method_info = self._extract_function_info(child)
                class_info['methods'].append(method_info)
        
        return class_info
    
    def _extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Extract information about a function or method.
        
        Args:
            node: AST node for the function
            
        Returns:
            Dictionary with function information
        """
        function_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'parameters': []
        }
        
        # Extract parameters
        for arg in node.args.args:
            # Skip 'self' and 'cls'
            if arg.arg in ('self', 'cls'):
                continue
                
            param = {'name': arg.arg}
            
            # Get default value if available
            if node.args.defaults:
                defaults_start = len(node.args.args) - len(node.args.defaults)
                arg_index = node.args.args.index(arg)
                if arg_index >= defaults_start:
                    default_index = arg_index - defaults_start
                    param['default'] = self._get_default_value(node.args.defaults[default_index])
            
            function_info['parameters'].append(param)
        
        # Extract type hints from annotations
        type_hints = {}
        for arg in node.args.args:
            if arg.annotation:
                type_hints[arg.arg] = self._get_name(arg.annotation)
        
        if node.returns:
            type_hints['return'] = self._get_name(node.returns)
            
        function_info['type_hints'] = type_hints
        
        # Extract return type from docstring
        if function_info['docstring']:
            return_match = re.search(r'Returns:\s*(.*?)(?:\n\s*\n|\Z)', function_info['docstring'], re.DOTALL)
            if return_match:
                function_info['returns'] = return_match.group(1).strip()
        
        return function_info
    
    def _get_name(self, node) -> str:
        """Get name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Index):
            return self._get_name(node.value)
        elif isinstance(node, ast.Tuple):
            return ', '.join(self._get_name(elt) for elt in node.elts)
        elif isinstance(node, str):
            return node
        elif hasattr(node, 'value'):
            return str(node.value)
        else:
            return str(node)
    
    def _get_default_value(self, node) -> str:
        """Get default value from an AST node."""
        if isinstance(node, ast.Str):
            return f"'{node.s}'"
        elif isinstance(node, ast.Num):
            return str(node.n)
        elif isinstance(node, ast.NameConstant):
            return str(node.value)
        elif isinstance(node, ast.List):
            return f"[{', '.join(self._get_default_value(elt) for elt in node.elts)}]"
        elif isinstance(node, ast.Dict):
            keys = [self._get_default_value(k) for k in node.keys]
            values = [self._get_default_value(v) for v in node.values]
            items = [f"{k}: {v}" for k, v in zip(keys, values)]
            return f"{{{', '.join(items)}}}"
        elif isinstance(node, ast.Tuple):
            return f"({', '.join(self._get_default_value(elt) for elt in node.elts)})"
        elif isinstance(node, ast.Call):
            return f"{self._get_name(node.func)}(...)"
        else:
            return "..."
    
    def _format_documentation(self, module_path: str, docstring: str,
                           classes: List[Dict[str, Any]], 
                           functions: List[Dict[str, Any]]) -> str:
        """
        Format documentation content.
        
        Args:
            module_path: Module import path
            docstring: Module docstring
            classes: List of class information
            functions: List of function information
            
        Returns:
            Formatted documentation content
        """
        # Format module header
        content = f"# {os.path.basename(module_path)}\n\n"
        
        # Add module docstring
        if docstring:
            content += f"{docstring}\n\n"
        
        # Add module import path
        content += f"**Module Path:** `{module_path}`\n\n"
        
        # Add table of contents
        content += "## Table of Contents\n\n"
        
        if classes:
            content += "### Classes\n\n"
            for cls in classes:
                content += f"- [{cls['name']}](#{cls['name'].lower()})\n"
            content += "\n"
        
        if functions:
            content += "### Functions\n\n"
            for func in functions:
                content += f"- [{func['name']}](#{func['name'].lower()})\n"
            content += "\n"
        
        # Add classes
        if classes:
            content += "## Classes\n\n"
            for cls in classes:
                content += self._format_class(cls)
        
        # Add functions
        if functions:
            content += "## Functions\n\n"
            for func in functions:
                content += self._format_function(func)
        
        return content
    
    def _format_class(self, cls: Dict[str, Any]) -> str:
        """
        Format class documentation.
        
        Args:
            cls: Class information
            
        Returns:
            Formatted class documentation
        """
        content = f"### {cls['name']}\n\n"
        
        # Add inheritance
        if cls['bases']:
            content += f"**Inherits from:** {', '.join(cls['bases'])}\n\n"
        
        # Add docstring
        if cls['docstring']:
            content += f"{cls['docstring']}\n\n"
        
        # Add methods
        if cls['methods']:
            content += "#### Methods\n\n"
            for method in cls['methods']:
                # Skip special methods
                if method['name'].startswith('__') and method['name'] != '__init__':
                    continue
                    
                content += self._format_method(method)
        
        return content
    
    def _format_method(self, method: Dict[str, Any]) -> str:
        """
        Format method documentation.
        
        Args:
            method: Method information
            
        Returns:
            Formatted method documentation
        """
        # Generate method signature
        params_str = ', '.join([
            f"{param['name']}={param.get('default', '')}" if 'default' in param else param['name']
            for param in method['parameters']
        ])
        
        if method['name'] == '__init__':
            content = f"##### `__init__({params_str})`\n\n"
        else:
            content = f"##### `{method['name']}({params_str})`\n\n"
        
        # Add docstring
        if method['docstring']:
            content += f"{method['docstring']}\n\n"
        
        # Add parameter types and return type
        if method['type_hints']:
            content += "**Type Hints:**\n\n"
            for param_name, type_hint in method['type_hints'].items():
                if param_name == 'return':
                    content += f"- **returns**: `{type_hint}`\n"
                else:
                    content += f"- **{param_name}**: `{type_hint}`\n"
            content += "\n"
        
        return content
    
    def _format_function(self, func: Dict[str, Any]) -> str:
        """
        Format function documentation.
        
        Args:
            func: Function information
            
        Returns:
            Formatted function documentation
        """
        # Generate function signature
        params_str = ', '.join([
            f"{param['name']}={param.get('default', '')}" if 'default' in param else param['name']
            for param in func['parameters']
        ])
        
        content = f"### {func['name']}\n\n"
        content += f"```python\n{func['name']}({params_str})\n```\n\n"
        
        # Add docstring
        if func['docstring']:
            content += f"{func['docstring']}\n\n"
        
        # Add parameter types and return type
        if func['type_hints']:
            content += "**Type Hints:**\n\n"
            for param_name, type_hint in func['type_hints'].items():
                if param_name == 'return':
                    content += f"- **returns**: `{type_hint}`\n"
                else:
                    content += f"- **{param_name}**: `{type_hint}`\n"
            content += "\n"
        
        return content
    
    def _generate_index(self):
        """Generate index page with links to all documentation files."""
        # Find all Markdown files in the output directory
        md_files = []
        
        for root, _, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.output_dir)
                    md_files.append(rel_path)
        
        # Sort files
        md_files.sort()
        
        # Generate index content
        content = "# AI Portfolio Manager Documentation\n\n"
        
        # Add project description
        try:
            readme_path = os.path.join(self.source_dir, '..', 'readme.md')
            if os.path.exists(readme_path):
                with open(readme_path, 'r') as f:
                    readme = f.read()
                
                # Extract first paragraph from README
                match = re.search(r'^# .+?\n\n(.+?)(\n\n|\Z)', readme, re.DOTALL)
                if match:
                    content += f"{match.group(1)}\n\n"
        except Exception:
            pass
        
        content += "## Modules\n\n"
        
        # Group files by directory
        groups = {}
        for file in md_files:
            dir_name = os.path.dirname(file)
            if not dir_name:
                dir_name = "root"
            
            if dir_name not in groups:
                groups[dir_name] = []
                
            groups[dir_name].append(file)
        
        # Add links grouped by directory
        for dir_name, files in sorted(groups.items()):
            if dir_name == "root":
                group_header = "Core Modules"
            else:
                group_header = f"{dir_name.replace('/', '.')} Package"
                
            content += f"### {group_header}\n\n"
            
            for file in sorted(files):
                # Get module name without extension
                module_name = os.path.basename(file).replace('.md', '')
                
                # Create link
                content += f"- [{module_name}]({file})\n"
            
            content += "\n"
        
        # Save index file
        index_path = os.path.join(self.output_dir, 'index.md')
        with open(index_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Index file generated at {index_path}")
    
    def generate_html_documentation(self):
        """Convert Markdown documentation to HTML."""
        # Find all Markdown files
        md_files = []
        
        for root, _, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    md_files.append(file_path)
        
        # Convert each file
        for md_file in md_files:
            self._convert_to_html(md_file)
        
        # Create HTML index
        index_path = os.path.join(self.output_dir, 'index.md')
        if os.path.exists(index_path):
            self._convert_to_html(index_path)
            
            # Rename to index.html
            html_path = index_path.replace('.md', '.html')
            if os.path.exists(html_path):
                index_html = os.path.join(self.output_dir, 'index.html')
                if html_path != index_html:
                    os.rename(html_path, index_html)
    
    def _convert_to_html(self, md_file: str):
        """
        Convert Markdown file to HTML.
        
        Args:
            md_file: Path to Markdown file
        """
        # Output file path
        html_file = md_file.replace('.md', '.html')
        
        try:
            # Read Markdown content
            with open(md_file, 'r') as f:
                md_content = f.read()
            
            # Convert to HTML
            html_content = markdown.markdown(
                md_content,
                extensions=['fenced_code', 'tables', 'toc']
            )
            
            # Add styling
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(md_file).replace('.md', '')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 24px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        pre {{
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }}
        code {{
            background-color: #f8f8f8;
            border-radius: 3px;
            padding: 3px 5px;
            font-family: Consolas, monospace;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        blockquote {{
            padding: 0 16px;
            color: #777;
            border-left: 4px solid #ddd;
            margin: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        table, th, td {{
            border: 1px solid #ddd;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
            
            # Save HTML file
            with open(html_file, 'w') as f:
                f.write(html)
            
            logger.debug(f"Converted {md_file} to HTML")
            
        except Exception as e:
            logger.error(f"Failed to convert {md_file} to HTML: {e}")


# Command-line interface for generating documentation
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate documentation')
    parser.add_argument('--source-dir', type=str, required=True,
                        help='Source code directory')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for documentation')
    parser.add_argument('--html', action='store_true',
                        help='Generate HTML documentation')
    
    args = parser.parse_args()
    
    generator = DocumentationGenerator(args.source_dir, args.output_dir)
    generator.generate_documentation()
    
    if args.html:
        generator.generate_html_documentation()