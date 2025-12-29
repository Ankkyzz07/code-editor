from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_safe_execution():
    """Test that safe code runs correctly."""
    response = client.post("/execute", json={"code": "print('Safe')"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "Safe" in data["report"]["output"]

def test_security_block_file():
    """Test that file access is blocked."""
    code = "open('/etc/hosts')"
    response = client.post("/execute", json={"code": code})
    assert response.status_code == 200
    data = response.json()
    
    # Check if the sandbox reported the block
    # Note: Depending on logic, it might be in 'file_access' log or an error
    logs = data["report"]
    assert any("BLOCKED" in access for access in logs.get("file_access", [])) or \
           "Access to file" in logs.get("error", "")

def test_security_block_import():
    """Test that dangerous imports are blocked."""
    code = "import os"
    response = client.post("/execute", json={"code": code})
    assert response.status_code == 200
    data = response.json()
    
    logs = data["report"]
    # Check for the error message in the error field OR the logs
    error_msg = str(logs.get("error", ""))
    
    # Match the text from our new sandbox.py
    assert "Import 'os' is banned" in error_msg
    
def test_timeout():
    """Test that infinite loops are killed."""
    # This loop runs forever
    code = "while True: pass"
    response = client.post("/execute", json={"code": code})
    
    # We expect a 408 Timeout error
    assert response.status_code == 408
    assert "Execution timed out" in response.json()["detail"]