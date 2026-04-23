import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def setup_portable_msvc():
    msvc_dir = Path(__file__).parent / "msvc_portable"
    if msvc_dir.exists():
        return str(msvc_dir)

    print("Downloading portable MSVC downloader...")
    script_url = "https://gist.githubusercontent.com/mmozeiko/7f3162ec2988e81e56d5c4e22cde9977/raw/portable-msvc.py"
    downloader_script = Path(__file__).parent / "portable-msvc.py"
    import requests
    response = requests.get(script_url)
    response.raise_for_status()
    downloader_script.write_bytes(response.content)

    print("Extracting MSVC (this will take a while)...")
    # This downloads the actual compiler binaries into the msvc_portable folder
    subprocess.check_call([sys.executable, str(downloader_script)], cwd=Path(__file__).parent)

    return str(msvc_dir)

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

    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'certifi', 'pip'])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'certifi'])

    # msvc_path = setup_portable_msvc() # uncomment if you do not have visual studio installed

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
        "DISTUTILS_USE_SDK": "1",
        "MSSDK": "1",
    # uncomment if you do not have visual studio installed
    #    "PATH": f"{msvc_path}/bin/x64;" + os.environ["PATH"] # Add portable compiler to PATH
    }
    subprocess.check_call(
        ["cmake", "-G", "Visual Studio 18 2026", "-S", ".", "-B", "build", "-DPYBIND11_FINDPYTHON=ON"],
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
