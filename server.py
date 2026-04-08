from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
from typing import List, Optional

app = FastAPI(title="AI-IR-Toolkit Bridge", version="1.0")

class ToolRequest(BaseModel):
    tool: str
    args: List[str] = []
    timeout: Optional[int] = 60

# Whitelisted IR/forensics tools (add more later)
ALLOWED_TOOLS = {
    "sha256sum", "strings", "file", "binwalk", "volatility3",
    "tshark", " foremost", "exiftool", "bulk_extractor"
}

@app.get("/health")
async def health():
    return {"status": "online", "toolkit": "ai-ir-toolkit", "phase": "3"}

@app.post("/execute")
async def execute_tool(req: ToolRequest):
    if req.tool not in ALLOWED_TOOLS:
        return {"error": f"Tool '{req.tool}' not allowed for security"}

    cmd = [req.tool] + req.args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=req.timeout
        )
        return {
            "tool": req.tool,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except Exception as e:
        return {"error": str(e)}
