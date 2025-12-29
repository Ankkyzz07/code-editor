# Metron Code Editor - Secure Sandbox Engine

## Overview
A secure Python execution environment designed to safely run untrusted user code. It uses a multi-layered security approach:
1. **Application Layer:** Monkey-patching `builtins` to restrict file and network access.
2. **System Layer:** Dedicated subprocesses with strict timeouts.
3. **Infrastructure Layer:** Docker containerization with non-root privileges.

## Project Structure
- `src/sandbox.py`: The restricted execution environment (The "Prisoner").
- `src/api.py`: REST API that manages the lifecycle of the sandbox (The "Jailer").

## How to Run
### 1. Local Development
```bash
pip install -r requirements.txt
python src/api.py