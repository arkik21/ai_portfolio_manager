# utility.logging_utility

Logging Utility Module

This module provides centralized logging configuration for all components.

**Module Path:** `utility.logging_utility`

## Table of Contents

### Classes

- [LoggingManager](#loggingmanager)

### Functions

- [get_logger](#get_logger)
- [configure_logging](#configure_logging)

## Classes

### LoggingManager

Manages logging configuration across the application.

#### Methods

##### `__init__(log_dir=None, log_level='info', log_to_console=True, log_to_file=True)`

Initialize the LoggingManager.

Args:
    log_dir: Directory to store log files (default: ./logs)
    log_level: Logging level (debug, info, warning, error, critical)
    log_to_console: Whether to output logs to console
    log_to_file: Whether to output logs to file

**Type Hints:**

- **log_dir**: `str`
- **log_level**: `str`
- **log_to_console**: `bool`
- **log_to_file**: `bool`

##### `configure_root_logger(log_to_console, log_to_file)`

Configure the root logger with console and/or file handlers.

**Type Hints:**

- **log_to_console**: `bool`
- **log_to_file**: `bool`

##### `get_logger(name, module_log_level=None)`

Get a logger for a specific module.

Args:
    name: Logger name (typically module name)
    module_log_level: Optional specific log level for this module
    
Returns:
    Configured logger instance

**Type Hints:**

- **name**: `str`
- **module_log_level**: `Optional[str]`
- **returns**: `logging.Logger`

##### `set_global_log_level(log_level)`

Change the log level for all configured loggers.

Args:
    log_level: New log level (debug, info, warning, error, critical)

**Type Hints:**

- **log_level**: `str`

## Functions

### get_logger

```python
get_logger(name, module_log_level=None)
```

Get a logger for a specific module.

Args:
    name: Logger name (typically module name)
    module_log_level: Optional specific log level for this module
    
Returns:
    Configured logger instance

**Type Hints:**

- **name**: `str`
- **module_log_level**: `Optional[str]`
- **returns**: `logging.Logger`

### configure_logging

```python
configure_logging(log_dir=None, log_level='info', log_to_console=True, log_to_file=True)
```

Configure global logging settings.

Args:
    log_dir: Directory to store log files
    log_level: Logging level (debug, info, warning, error, critical)
    log_to_console: Whether to output logs to console
    log_to_file: Whether to output logs to file

**Type Hints:**

- **log_dir**: `str`
- **log_level**: `str`
- **log_to_console**: `bool`
- **log_to_file**: `bool`

