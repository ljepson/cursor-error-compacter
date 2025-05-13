# Error Log Formatter

A utility tool for formatting Cursor IDE "Problem Window" errors into something that can be passed to your LLM of choice, but using less tokens. This tool is especially useful for processing diagnostic output from code editors like Cursor or VS Code.

## Features

- Colorized terminal output (when colorama is installed)
- Convert JSON diagnostic logs into compact, readable text format
- Customizable path depth for clearer file identification 
- Extract key information: file paths, line numbers, error codes, and messages
- Handles various JSON formats and encodings
- Intelligently parses error/warning/info levels based on severity
- Option to save results to clipboard
- Safeguard against overwriting existing files
- Severity filtering to focus on errors or warnings
- Silent mode for script integration
- Summary reporting showing counts of errors/warnings/info messages
- Support for reading input from files, command line, STDIN pipes, or clipboard

## Installation

1. Clone this repository:

   ```sh
   git clone https://github.com/ljepson/cursor-error-compacter.git

   cd cursor-error-compacter
   ```

2. Optional: Install clipboard support:

   ```sh
   python -mvenv .venv

   . .venv/bin/activate

   pip install pyperclip
   ```

3. Optional: Install colorized output support:

   ```sh
   python -mvenv .venv

   . .venv/bin/activate

   pip install colorama
   ```

## Usage

### Basic Usage

Process a JSON file:

```sh
python formatter.py example.json
```

Specify an output file:

```sh
python formatter.py example.json -o output.txt
```

### Advanced Usage

Read from clipboard:

```sh
python formatter.py -p
```

Copy results to clipboard in addition to saving to file:

```sh
python formatter.py example.json -c
```

Force overwrite of existing output file:

```sh
python formatter.py example.json -o output.txt --force
```

Show verbose output:

```sh
python formatter.py example.json -v
```

Filter by severity level (show only warnings and errors):

```sh
python formatter.py example.json --min-severity 4
```

Include more path information to differentiate files:

```sh
python formatter.py example.json --path-depth 2
```

Disable colored output:

```sh
python formatter.py example.json --no-color
```

Run silently (for script integration):

```sh
python formatter.py example.json -s
```

Pipe content from another command:

```sh
cat example.json | python formatter.py
```

### Command Line Options

```txt
usage: formatter.py [-h] [-o OUTPUT] [-c] [-p] [-v] [-s] [--force] [--min-severity MIN_SEVERITY] [--path-depth PATH_DEPTH]
                    [--no-color]
                    [input]

Format error logs from JSON to a more compact format

positional arguments:
  input                 Input JSON file or content

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Output file name (default: formatted_errors.txt)
  -c, --clipboard       Copy output to clipboard
  -p, --paste           Read input from clipboard
  -v, --verbose         Show detailed output
  -s, --silent          Suppress all output except errors
  --force               Overwrite output file if it exists
  --min-severity MIN_SEVERITY
                        Minimum severity level (0-10, where 8+ is error, 4+ is warning)
  --path-depth PATH_DEPTH
                        Number of path components to include (default: 1=filename only)
  --no-color            Disable colored output
  ```

## Example

Given a JSON error log like this:

```json
[{
    "resource": "/path/to/file.lua",
    "code": "redundant-parameter",
    "severity": 4,
    "message": "This function expects a maximum of 0 argument(s) but instead it is receiving 1.",
    "source": "Lua Diagnostics.",
    "startLineNumber": 180,
    "startColumn": 19,
    "endLineNumber": 180,
    "endColumn": 35
}]
```

The formatter will output:

```
WARNING [file.lua:180] redundant-parameter: This function expects a maximum of 0 argument(s) but instead it is receiving 1.
```

With `--path-depth 2`, you'll get:

```
WARNING [to/file.lua:180] redundant-parameter: This function expects a maximum of 0 argument(s) but instead it is receiving 1.
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
