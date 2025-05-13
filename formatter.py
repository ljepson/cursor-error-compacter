#!/usr/bin/env python3
import json
import sys
import os
import re
import argparse
from pathlib import Path

# Try to import clipboard modules if available
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

# Try to import colorama for terminal colors
try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama
    HAS_COLORS = True
except ImportError:
    HAS_COLORS = False

def is_valid_json(content):
    """Check if content is valid JSON."""
    try:
        json.loads(content)
        return True
    except json.JSONDecodeError:
        # If not valid JSON, try to see if it's a fragment or array of JSON objects
        try:
            json.loads(f"[{content}]")
            return True
        except json.JSONDecodeError:
            try:
                # Check if we can parse each line as JSON separately
                for line in content.strip().split('\n'):
                    if line.strip():
                        json.loads(line)
                return True
            except json.JSONDecodeError:
                return False

def process_file(file_path, max_path_depth=1, min_severity=0):
    """Process file with regex approach to find and format error messages."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return [], {"ERROR": 0, "WARNING": 0, "INFO": 0, "TOTAL": 0}
    
    # Check if content is valid JSON
    if not is_valid_json(content):
        print(f"Warning: File {file_path} doesn't appear to contain valid JSON")
        print("Processing anyway, but results may be incomplete.")
    
    results = []
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "TOTAL": 0}
    
    # Use regex to find error message blocks
    pattern = r'\{\s*"resource":.+?(?:,"modelVersionId":[^,}]+)?\}'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        block = match.group(0)
        
        # Extract information
        resource_match = re.search(r'"resource"\s*:\s*"([^"]+)"', block)
        severity_match = re.search(r'"severity"\s*:\s*(\d+)', block)
        message_match = re.search(r'"message"\s*:\s*"([^"]*)"', block)
        code_match = re.search(r'"code"\s*:\s*"?([^",}]+)"?', block)
        line_match = re.search(r'"startLineNumber"\s*:\s*(\d+)', block)
        
        if resource_match and message_match:
            # Get filepath with configurable depth
            path_parts = resource_match.group(1).replace('\\', '/').split('/')
            if max_path_depth > 0 and len(path_parts) > max_path_depth:
                file_path = '/'.join(path_parts[-max_path_depth:])
            else:
                file_path = path_parts[-1]
            
            # Determine message type based on severity
            severity = int(severity_match.group(1)) if severity_match else 0
            
            # Apply severity filter
            if severity < min_severity:
                continue
                
            msg_type = "ERROR" if severity >= 8 else "WARNING" if severity >= 4 else "INFO"
            counts[msg_type] += 1
            counts["TOTAL"] += 1
            
            # Get line number
            line = line_match.group(1) if line_match else "?"
            
            # Get code
            code = code_match.group(1) if code_match else ""
            
            # Get message and cleanup any escaping
            message = message_match.group(1).replace('\\`', '`')
            message = message.replace('\\n', ' ')  # Replace newlines with spaces for better readability
            
            # Format output
            compact = f"{msg_type} [{file_path}:{line}] {code}: {message}"

            results.append(compact)
    
    return results, counts

def colorize(text):
    """Add color to text based on severity if colorama is available."""
    if not HAS_COLORS:
        return text
    
    if "ERROR" in text:
        return f"{Fore.RED}{text}{Style.RESET_ALL}"
    elif "WARNING" in text:
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    elif "INFO" in text:
        return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
    return text

def get_unique_filename(base_filename):
    """Generate a unique filename by adding a number if file exists."""
    if not os.path.exists(base_filename):
        return base_filename
    
    path = Path(base_filename)
    directory, filename = path.parent, path.name
    name, extension = os.path.splitext(filename)
    
    # Check if name already ends with a number
    match = re.search(r'^(.*?)(\d+)$', name)

    if match:
        name_base, num = match.groups()
        counter = int(num)
    else:
        name_base, counter = name, 0
    
    # Increment counter until we find an unused filename
    while True:
        counter += 1
        new_filename = f"{name_base}{counter}{extension}"
        new_path = directory / new_filename
        if not os.path.exists(new_path):
            return str(new_path)

def main():
    """Main function to process error logs."""
    parser = argparse.ArgumentParser(description="Format error logs from JSON to a more compact format")
    parser.add_argument("input", nargs="?", help="Input JSON file or content")
    parser.add_argument("-o", "--output", help="Output file name (default: formatted_errors.txt)")
    parser.add_argument("-c", "--clipboard", action="store_true", help="Copy output to clipboard")
    parser.add_argument("-p", "--paste", action="store_true", help="Read input from clipboard")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress all output except errors")
    parser.add_argument("--force", action="store_true", help="Overwrite output file if it exists")
    parser.add_argument("--min-severity", type=int, default=0, 
                        help="Minimum severity level (0-10, where 8+ is error, 4+ is warning)")
    parser.add_argument("--path-depth", type=int, default=1, 
                        help="Number of path components to include (default: 1=filename only)")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    
    args = parser.parse_args()
    
    # Disable colors if requested
    global HAS_COLORS
    if args.no_color:
        HAS_COLORS = False
    
    # Setup default output file
    output_file = args.output or "formatted_errors.txt"

    if not args.force:
        output_file = get_unique_filename(output_file)

    if not HAS_CLIPBOARD and (args.paste or args.clipboard) and not args.silent:
        print("Warning: Clipboard module not found. Please install pyperclip to use clipboard functionality.")
        print(f"Proceeding with saving to {output_file}")
    
    # Process input from various sources
    results = []
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "TOTAL": 0}
    
    try:
        if args.paste and HAS_CLIPBOARD:
            # Get content from clipboard
            try:
                content = pyperclip.paste()
                if not args.silent:
                    print("Reading from clipboard...")
                
                # Write content to a temp file
                temp_file = "temp_content.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Process the temp file
                results, counts = process_file(temp_file, args.path_depth, args.min_severity)
                
                # Clean up
                try:
                    os.remove(temp_file)
                except:
                    if not args.silent:
                        print("Error removing temp file - Remove temp_content.json manually")
                
            except Exception as e:
                print(f"Error reading from clipboard: {e}")
                return
                
        elif args.input:
            # Check if argument is a file that exists
            if os.path.isfile(args.input):
                file_path = args.input
                results, counts = process_file(file_path, args.path_depth, args.min_severity)
            else:
                # Treat as direct content
                content = args.input
                
                # Write content to a temp file
                temp_file = "temp_content.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Process the temp file
                results, counts = process_file(temp_file, args.path_depth, args.min_severity)
                
                # Clean up
                try:
                    os.remove(temp_file)
                except:
                    if not args.silent:
                        print("Error removing temp file - Remove temp_content.json manually")
        else:
            # Try to read from stdin if no arguments provided
            if not sys.stdin.isatty():
                content = sys.stdin.read()
                
                # Write content to a temp file
                temp_file = "temp_content.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Process the temp file
                results, counts = process_file(temp_file, args.path_depth, args.min_severity)
                
                # Clean up
                try:
                    os.remove(temp_file)
                except:
                    if not args.silent:
                        print("Error removing temp file - Remove temp_content.json manually")
            else:
                parser.print_help()
                print("\nNo input provided. Use a file, direct content, or pipe input.")
                return
        
        # Write results to file
        if results:
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in results:
                    if args.verbose and not args.silent:
                        print(colorize(result))
                    f.write(result + "\n")
            
            # Show summary information if not silent
            if not args.silent:
                print(f"Results saved to {output_file}")
                print(f"Summary: {counts['TOTAL']} messages processed")
                if counts["ERROR"] > 0:
                    print(f"  - {counts['ERROR']} errors")
                if counts["WARNING"] > 0:
                    print(f"  - {counts['WARNING']} warnings")
                if counts["INFO"] > 0:
                    print(f"  - {counts['INFO']} info messages")
            
            # Copy to clipboard if requested and available
            if args.clipboard and HAS_CLIPBOARD:
                try:
                    clipboard_content = "\n".join(results)
                    pyperclip.copy(clipboard_content)
                    if not args.silent:
                        print("Results copied to clipboard")
                except Exception as e:
                    print(f"Error copying to clipboard: {e}")
        else:
            if not args.silent:
                print("No valid error messages found in input")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())