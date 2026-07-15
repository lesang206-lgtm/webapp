import os
import sys
import zipfile
import shutil
from pathlib import Path

import gdown

BASE_DIR = Path(__file__).parent.parent
MARKER_FILE = BASE_DIR / 'webapp' / '.setup_done'
KIANA_AOV_DIR = BASE_DIR / 'KIANA_AOV'

GDRIVE_KIANA_ID = os.environ.get('GDRIVE_KIANA_ID', '1gIDPurG0NJWQOYtz5BjwUfD56Ql3z205')
GDRIVE_V7_ID = os.environ.get('GDRIVE_V7_ID', '1EV7nWY8pHfhACm8cZDIa5ZWqOKgKuBsL')


def download_gdrive_file(file_id, dest_path):
    print(f"  Downloading {file_id}...")
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, str(dest_path), quiet=False)

    if not dest_path.exists() or dest_path.stat().st_size == 0:
        raise Exception(f"Download failed for {file_id}")

    print(f"  Downloaded: {dest_path.name} ({dest_path.stat().st_size / 1024 / 1024:.1f} MB)")


def extract_zip(zip_path, extract_to):
    print(f"  Extracting {zip_path.name}...")
    if not zipfile.is_zipfile(zip_path):
        raise Exception(f"Not a valid zip file: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)


def fix_nested_structure():
    res_dir = KIANA_AOV_DIR / 'Resources'
    if not res_dir.exists():
        return

    for version_dir in res_dir.iterdir():
        if not version_dir.is_dir():
            continue
        inner_res = version_dir / 'Resources'
        if inner_res.exists():
            print(f"  Fixing nested structure in {version_dir.name}...")
            for item in inner_res.iterdir():
                dest = version_dir / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
            shutil.rmtree(inner_res)


def setup_kiana_aov():
    if KIANA_AOV_DIR.exists():
        res_dir = KIANA_AOV_DIR / 'Resources'
        if res_dir.exists() and any(res_dir.iterdir()):
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

    fix_nested_structure()

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
