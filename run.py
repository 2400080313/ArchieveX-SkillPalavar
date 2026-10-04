"""
ArchiveX - Application Launcher
Executes the Streamlit application with optimized default flags.
"""
import sys
import subprocess
from pathlib import Path

def main():
    app_path = Path(__file__).resolve().parent / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        "--server.port=8501"
    ]
    print(f"Starting ArchiveX on http://localhost:8501 ...")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nArchiveX stopped.")

if __name__ == "__main__":
    main()
