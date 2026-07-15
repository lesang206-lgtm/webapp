import json
import secrets
from datetime import datetime
from pathlib import Path

import requests


class KeyManager:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self._load_db()

    def _load_db(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    self.db = json.load(f)
            except Exception:
                self.db = {}
        else:
            self.db = {}

    def _save_db(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.db, f, indent=2)

    def generate_key(self, ip):
        ngay = int(datetime.now().day)
        key1 = str(ngay * 27 + 27)
        ip_numbers = ''.join(filter(str.isdigit, ip))
        key = f'NDK{key1}{ip_numbers}'
        expiration = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        return key, expiration

    def validate_key(self, ip, key):
        key = key.strip().upper()
        self._load_db()
        if key in self.db:
            entry = self.db[key]
            exp = datetime.fromisoformat(entry['expiration'])
            if exp > datetime.now():
                entry['last_used'] = datetime.now().isoformat()
                self._save_db()
                return True
            else:
                del self.db[key]
                self._save_db()
        return False

    def save_key(self, ip, key, expiration):
        self.db[key] = {
            'ip': ip,
            'expiration': expiration.isoformat(),
            'created': datetime.now().isoformat(),
        }
        self._save_db()

    def has_valid_key(self, ip):
        self._load_db()
        now = datetime.now()
        for key, entry in list(self.db.items()):
            exp = datetime.fromisoformat(entry['expiration'])
            if exp > now:
                return True
        return False

    def shorten_url(self, url, token):
        if not token:
            return None
        try:
            api_url = f'https://link4m.co/api-shorten/v2?api={token}&url={url}'
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('shortenedUrl')
        except Exception:
            pass
        return None
