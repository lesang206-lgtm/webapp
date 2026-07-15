import json
import hashlib
import secrets
from datetime import datetime, timedelta
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
        now = datetime.now()
        day_part = now.day * 31 + 7
        rand_part = secrets.token_hex(3)
        raw = f'km-{day_part}-{rand_part}-{ip}'
        key_hash = hashlib.md5(raw.encode()).hexdigest()[:8].upper()
        key = f'KM{day_part}{key_hash}'
        expiration = now.replace(hour=23, minute=59, second=59, microsecond=0)
        return key, expiration

    def validate_key(self, ip, key):
        calculated_key, exp = self.generate_key(ip)
        if calculated_key == key and exp > datetime.now():
            self.save_key(ip, key, exp)
            return True
        return False

    def save_key(self, ip, key, expiration):
        self.db[ip] = {
            'key': key,
            'expiration': expiration.isoformat(),
            'created': datetime.now().isoformat(),
        }
        self._save_db()

    def has_valid_key(self, ip):
        if ip in self.db:
            entry = self.db[ip]
            exp = datetime.fromisoformat(entry['expiration'])
            return exp > datetime.now()
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
