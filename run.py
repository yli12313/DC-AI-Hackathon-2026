#!/usr/bin/env python3
"""
World Cup 2026 Prediction Workflow - Startup Script
"""

import uvicorn
import sys
from pathlib import Path


def main():
    """Run the FastAPI server"""
    port = 8000
    host = "0.0.0.0"
    
    # Change to project directory
    project_dir = Path(__file__).parent
    import os
    os.chdir(project_dir)
    
    print("=" * 60)
    print("World Cup 2026 Prediction Workflow")
    print("=" * 60)
    print(f"\nStarting server on http://{host}:{port}")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nServer stopped. Goodbye!")
        sys.exit(0)
