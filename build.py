import subprocess
import argparse
from pathlib import Path

PROJECT_NAME = "secure-box"
MAIN_FILE = "main.py"
DIST_DIR = Path("dist")

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
    if DIST_DIR.exists():
        for p in DIST_DIR.iterdir():
            p.unlink()
        print("dist/ cleaned.")
    else:
        print("dist/ directory does not exist.")

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
