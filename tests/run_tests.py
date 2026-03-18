import subprocess
import sys
import os

def main():
    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run([sys.executable, "-m", "pytest", os.path.join(addon_dir, "tests"), "-v"], cwd=addon_dir)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
