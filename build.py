import subprocess
import argparse
import shutil
from pathlib import Path

PROJECT_NAME = "secure-box"
MAIN_FILE = "src/secure_box/cli.py"
DIST_DIR = Path("dist")
BUILD_DIR = Path("build")

def run(cmd):
    print("\n>>> Running:", " ".join(cmd), "\n")
    subprocess.run(cmd, check=True)

def build(release=False, upx=False):
    DIST_DIR.mkdir(exist_ok=True)

    cmd = [
        "python", "-m", "nuitka",
        "--onefile",
        "--standalone",
        "--follow-imports",
        "--output-dir=dist",
        f"--output-filename={PROJECT_NAME}",
        MAIN_FILE,
    ]

    if release:
        cmd.extend([
            "--lto=yes",
            "--enable-plugin=implicit-imports",
        ])

    if upx:
        cmd.extend([
            "--upx",
            "--upx-binary=upx",
        ])

    run(cmd)

def clean():
    """Clean build artifacts, logs, cache directories"""
    cleaned = []
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        cleaned.append("dist/")
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
        cleaned.append("logs/")


    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        cleaned.append("build")
    
    
    pytest_cache = Path(".pytest_cache")
    if pytest_cache.exists():
        shutil.rmtree(pytest_cache)
        cleaned.append(".pytest_cache/")
    
    pycache_count = 0
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache)
        pycache_count += 1
    if pycache_count > 0:
        cleaned.append(f"__pycache__/ ({pycache_count} adet)")
    
    pyc_count = 0
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
        pyc_count += 1
    if pyc_count > 0:
        cleaned.append(f"*.pyc ({pyc_count} adet)")
    
    nuitka_build = Path("main.build")
    if nuitka_build.exists():
        shutil.rmtree(nuitka_build)
        cleaned.append("main.build/")
    
    for egg_dir in Path(".").rglob("*.egg-info"):
        shutil.rmtree(egg_dir)
        cleaned.append(f"{egg_dir.name}")
    
    eggs_dir = Path(".eggs")
    if eggs_dir.exists():
        shutil.rmtree(eggs_dir)
        cleaned.append(".eggs/")
    
    if cleaned:
        print("Cleaned")
        for item in cleaned:
            print(f"  ✓ {item}")
    else:
        print("✨ Already clean!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true", help="Optimized build")
    parser.add_argument("--upx", action="store_true", help="UPX compress binary")
    parser.add_argument("--clean", action="store_true", help="Clean dist directory")

    args = parser.parse_args()

    if args.clean:
        clean()
    else:
        build(release=args.release, upx=args.upx)