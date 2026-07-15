import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
KIANA_AOV_DIR = BASE_DIR / "KIANA_AOV"
FILE_MOD_DIR = BASE_DIR / "File_mod"
V7_PY_PATH = BASE_DIR / "v7.py"

LINK4M_TOKEN = os.environ.get('LINK4M_TOKEN', '')

KEY_EXPIRY_HOURS = 24
MAX_SKINS = 20

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')

JOBS_DIR = BASE_DIR / "webapp" / "jobs"
JOBS_DIR.mkdir(exist_ok=True)

KEYS_DB = BASE_DIR / "webapp" / "keys.json"

GDRIVE_KIANA_ID = os.environ.get('GDRIVE_KIANA_ID', '1gIDPurG0NJWQOYtz5BjwUfD56Ql3z205')
GDRIVE_V7_ID = os.environ.get('GDRIVE_V7_ID', '1EV7nWY8pHfhACm8cZDIa5ZWqOKgKuBsL')
