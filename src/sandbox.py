import sys
import builtins
import json
import io
import contextlib
import os
import ast
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

POLICY_FILE = os.getenv("POLICY_FILE", "security_policy.json")
CONFIG_PATH = os.path.join(BASE_DIR, POLICY_FILE)

# Default Policy
POLICY = { "banned_modules": ["os", "sys"], "blocked_files": [] }

try:
    with open(CONFIG_PATH, 'r') as f:
        POLICY = json.load(f)
except FileNotFoundError:
    pass

# --- 2. LOGGING ---
activity_log = {
    "file_access": [], "imports": [], "output": "", "error": None, 
    "security_alerts": [] # List of all threats found
}

# --- 3. ANALYZER (AST Scanner with Line Numbers) ---
class SecurityScanner(ast.NodeVisitor):
    def __init__(self):
        self.banned = POLICY.get("banned_modules", [])
        self.violations = [] # Collection of errors

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.banned:
                self.violations.append(f"Line {node.lineno}: Direct import of '{alias.name}' detected.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module in self.banned:
            self.violations.append(f"Line {node.lineno}: Import from '{node.module}' detected.")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in ['eval', 'exec', 'compile']:
                 self.violations.append(f"Line {node.lineno}: Dangerous function '{node.func.id}()' detected.")
        self.generic_visit(node)

# --- 4. RUNTIME RESTRICTIONS (Fallback) ---
def secure_open(file, *args, **kwargs):
    filename = str(file)
    for blocked_item in POLICY.get("blocked_files", []):
        if blocked_item in filename:
            activity_log["file_access"].append(f"BLOCKED: {filename}")
            raise PermissionError(f"Access to '{filename}' denied.")
    return original_open(file, *args, **kwargs)

original_open = builtins.open
original_import = builtins.__import__

def secure_import(name, *args, **kwargs):
    activity_log["imports"].append(name)
    if name in POLICY.get("banned_modules", []):
        raise PermissionError(f"Import '{name}' is banned.")
    return original_import(name, *args, **kwargs)

builtins.open = secure_open
builtins.__import__ = secure_import

# --- 5. EXECUTION ENGINE ---
def run_user_code(code_string):
    output_buffer = io.StringIO()
    try:
        # STEP 1: Full Static Analysis
        tree = ast.parse(code_string)
        scanner = SecurityScanner()
        scanner.visit(tree)

        # If we found violations in the file, REPORT them and DO NOT RUN.
        if scanner.violations:
            activity_log["security_alerts"] = scanner.violations
            activity_log["error"] = "Static Analysis Failed: Malicious code detected."
            return # Stop execution here

        # STEP 2: If File is Clean, Run it
        with contextlib.redirect_stdout(output_buffer):
            exec(code_string, {'__builtins__': builtins})
            
    except SyntaxError as e:
        activity_log["error"] = f"Syntax Error: {e}"
    except PermissionError as e:
        activity_log["error"] = str(e)
    except Exception as e:
        activity_log["error"] = f"Runtime Error: {str(e)}"
    finally:
        activity_log["output"] = output_buffer.getvalue()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_user_code(sys.argv[1])
    else:
        activity_log["error"] = "No code provided."

    print(json.dumps(activity_log))