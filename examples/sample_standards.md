# Sample Coding Standards

This document demonstrates the format for defining coding standards that can be extracted by the tool.

## Naming Conventions

### Variables and Functions

- You must use `snake_case` for Python variable and function names
- You should use descriptive names that convey purpose
- Never use single-letter variable names except for loop counters (i, j, k)
- Do: Use verb phrases for function names (e.g., `calculate_total`, `validate_input`)
- Don't: Use abbreviations that aren't universally understood

### Classes and Types

1. Must use `PascalCase` for class names
2. Should prefix abstract classes with `Base` or `Abstract`
3. Required: Suffix exception classes with `Error` or `Exception`

## Code Formatting

### Indentation

- Must use 4 spaces for indentation (no tabs)
- Should align continuation lines with the opening delimiter

### Line Length

- Required: Maximum line length of 100 characters
- Recommended: Keep lines under 80 characters when possible

## Documentation Standards

### Docstrings

- Must include docstrings for all public modules, classes, and functions
- Should use Google-style or NumPy-style docstring format
- Always document parameters, return values, and raised exceptions

### Comments

- Prefer self-documenting code over comments
- Must explain "why" not "what" when comments are needed
- Never commit commented-out code

## Error Handling

### Exceptions

- Must catch specific exceptions, not bare `except`
- Should use custom exception classes for domain-specific errors
- Required: Log all caught exceptions with appropriate context

### Validation

1. Always validate input at system boundaries
2. Must sanitize user input before processing
3. Should fail fast with clear error messages

## Security Guidelines

### Credentials

- Never hardcode passwords, API keys, or secrets in source code
- Must use environment variables or secret management systems
- Required: Rotate credentials regularly

### Input Handling

- Must validate and sanitize all user input
- Should use parameterized queries for database operations
- Never trust client-side validation alone

## Testing Requirements

### Unit Tests

- Must write unit tests for all new functionality
- Required: Maintain minimum 80% code coverage
- Should use meaningful test names that describe the scenario

### Integration Tests

- Must test critical user workflows end-to-end
- Should mock external dependencies appropriately
- Consider using test fixtures for database state

## Performance Guidelines

### Database

- Should use connection pooling
- Must add indexes for frequently queried columns
- Avoid N+1 query patterns

### Caching

- Consider caching for expensive computations
- Must invalidate cache appropriately
- Should use TTL for time-sensitive data
