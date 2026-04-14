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

def generate_sub():
    fishing_dir = Path(__file__).parent / "fishing"

    build_dir = fishing_dir / "build"

    pyd_files = list(build_dir.rglob("*.pyd"))
    if not pyd_files:
        raise RuntimeError("No .pyd file found, build may have failed")
    print("Found pyd file")

    pyd_dir = str(pyd_files[0].parent)
    print(f"pyd_dir: {pyd_dir}")  # verify the path
    print(f"pyd files: {pyd_files}")  # verify it found the right file
    # Generate the stub
    subprocess.check_call([sys.executable, "-m", "pybind11_stubgen", "fish_multiple", "-o", str(pyd_dir)],
        env={**os.environ, "PYTHONPATH": pyd_dir})




def install():
    fishing_dir = Path(__file__).parent / "fishing"
    # Clean build completely
    shutil.rmtree(fishing_dir / "build", ignore_errors=True)
    ensure_cmake()
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install"])
    os.makedirs(fishing_dir / "build", exist_ok=True)
    env = {
        **os.environ,
        "Python3_ROOT_DIR": str(Path(sys.executable).parent.parent),
        "Python3_EXECUTABLE": sys.executable,
    }
    subprocess.check_call(
        ["cmake", "-G", "Visual Studio 17 2022", "-S", ".", "-B", "build", "-DPYBIND11_FINDPYTHON=ON"],
        cwd=Path(__file__).parent / "fishing",
        env=env
    )
    subprocess.run(
        ["cmake", "--build", "build"],
        cwd=fishing_dir,
        env=os.environ.copy()
    )

    # Install pybind11-stubgen if not already installed
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pybind11-stubgen"])

    generate_sub()

    print("Setup complete!")


if __name__ == "__main__":
    install()
