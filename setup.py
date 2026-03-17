import subprocess
import sys


def install():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install"])
    print("Setup complete!")


if __name__ == "__main__":
    install()
