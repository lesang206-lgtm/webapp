import os
import sys
import zipfile
import shutil
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.parent
MARKER_FILE = BASE_DIR / 'webapp' / '.setup_done'
KIANA_AOV_DIR = BASE_DIR / 'KIANA_AOV'

GDRIVE_KIANA_ID = os.environ.get('GDRIVE_KIANA_ID', '1FygINESUOVveLscX_2-waUZzMbYkFceV')
GDRIVE_V7_ID = os.environ.get('GDRIVE_V7_ID', '1EV7nWY8pHfhACm8cZDIa5ZWqOKgKuBsL')


def download_gdrive_file(file_id, dest_path):
    url = "https://drive.google.com/uc?export=download"
    session = requests.Session()

    print(f"  Downloading {file_id}...")
    response = session.get(url, params={'id': file_id}, stream=True)

    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break

    if token:
        response = session.get(url, params={'id': file_id, 'confirm': token}, stream=True)

    total = 0
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)
                total += len(chunk)

    print(f"  Downloaded: {dest_path.name} ({total / 1024 / 1024:.1f} MB)")


def extract_zip(zip_path, extract_to):
    print(f"  Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)


def setup_kiana_aov():
    if KIANA_AOV_DIR.exists() and any(KIANA_AOV_DIR.iterdir()):
        print("Resources already exists, skipping...")
        return

    print("Downloading resources...")
    zip_path = BASE_DIR / 'kiana_aov.zip'
    download_gdrive_file(GDRIVE_KIANA_ID, zip_path)
    extract_zip(zip_path, BASE_DIR)

    if not KIANA_AOV_DIR.exists():
        for item in BASE_DIR.iterdir():
            if item.is_dir() and 'KIANA' in item.name.upper():
                item.rename(KIANA_AOV_DIR)
                break

    if zip_path.exists():
        os.remove(zip_path)
    print("Resources ready!")


def setup_core():
    v7_path = BASE_DIR / 'v7.py'
    if v7_path.exists():
        print("Core already exists, skipping...")
        return

    print("Downloading core...")
    temp_path = BASE_DIR / 'core_temp.py'
    download_gdrive_file(GDRIVE_V7_ID, temp_path)
    shutil.move(temp_path, v7_path)
    print("Core ready!")


def main():
    if MARKER_FILE.exists():
        print("Setup already completed, skipping...")
        return

    print("=== Setting up ===")
    try:
        setup_kiana_aov()
        setup_core()
        MARKER_FILE.touch()
        print("=== Setup complete! ===")
    except Exception as e:
        print(f"Setup error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
