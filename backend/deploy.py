import os
import shutil
import zipfile
import subprocess
import sys

PACKAGE_DIR = "lambda-package"
ZIP_NAME = "lambda-deployment.zip"


def run(cmd):
    print(f"→ Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def clean():
    print("🧹 Cleaning previous builds...")
    shutil.rmtree(PACKAGE_DIR, ignore_errors=True)
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)


def create_package_dir():
    print("📁 Creating package directory...")
    os.makedirs(PACKAGE_DIR, exist_ok=True)


def install_dependencies():
    print("📦 Installing dependencies locally...")

    run([
        "pip",
        "install",
        "-r",
        "requirements.txt",
        "-t",
        PACKAGE_DIR,
        "--upgrade"
    ])


def copy_source_files():
    print("📄 Copying application files...")

    files = ["server.py", "lambda_handler.py", "context.py", "resources.py"]

    for file in files:
        if os.path.exists(file):
            shutil.copy2(file, PACKAGE_DIR)

    if os.path.exists("data"):
        shutil.copytree("data", f"{PACKAGE_DIR}/data")


def create_zip():
    print("🗜️ Creating deployment zip...")

    with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(PACKAGE_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, PACKAGE_DIR)
                zipf.write(full_path, arcname)


def show_size():
    size_mb = os.path.getsize(ZIP_NAME) / (1024 * 1024)
    print(f"✅ Package created: {ZIP_NAME} ({size_mb:.2f} MB)")


def main():
    try:
        print("🚀 Building Lambda deployment package...\n")

        clean()
        create_package_dir()
        install_dependencies()
        copy_source_files()
        create_zip()
        show_size()

        print("\n🎯 Build completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()