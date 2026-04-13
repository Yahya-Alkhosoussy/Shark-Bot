import os
import shutil
import subprocess
import sys
from pathlib import Path


def ensure_cmake():
    if shutil.which("cmake"):
        print("CMake already exists at: ", shutil.which("cmake"))
        return # Cmake exists

    print("cmake not found, installing via pip")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cmake"])

    # Add Pip's cmake to Path so it can be used imediately
    cmake_dir = Path(sys.executable).parent / "Scripts" # windows
    if not cmake_dir.exists():
        cmake_dir = Path(sys.executable).parent # Unix

    os.environ["PATH"] = str(cmake_dir) + os.pathsep + os.environ["PATH"]

    if not shutil.which("cmake"):
        raise RuntimeError("CMake installation failed")

    # Make sure it was installed correctly
    import cmake
    print(cmake.CMAKE_BIN_DIR) # shows where binary is

    print("CMake installed successfully")


def install():
    ensure_cmake()
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install"])
    os.makedirs(Path(__file__).parent / "fishing" / "build", exist_ok=True)
    subprocess.check_call(
        ["cmake", "-G", "Visual Studio 17 2022", "-S", ".", "-B", "build"], cwd=Path(__file__).parent / "fishing"
    )
    subprocess.check_call(
        ["cmake", "--build", "build"],
        cwd=Path(__file__).parent / "fishing"
    )

    print("Setup complete!")


if __name__ == "__main__":
    install()
