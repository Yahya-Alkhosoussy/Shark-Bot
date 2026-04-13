import os
import subprocess
import sys
from pathlib import Path


def install():
    print(Path(__file__).parent)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install"])
    if not os.path.exists("fishing/build"):
        subprocess.check_call(
            ["cmake", "-G", "Visual Studio 17", "-S", ".", "-B", "build"], cwd=Path(__file__).parent / "fishing"
        )

    print("Setup complete!")


if __name__ == "__main__":
    install()
