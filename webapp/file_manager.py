import shutil
from pathlib import Path
from datetime import datetime, timedelta


class FileManager:
    def __init__(self, output_dir, max_age_hours=24):
        self.output_dir = Path(output_dir)
        self.max_age_hours = max_age_hours

    def cleanup_old_files(self):
        now = datetime.now()
        if not self.output_dir.exists():
            return

        for item in self.output_dir.iterdir():
            if not item.is_dir():
                continue
            try:
                dir_time = datetime.fromtimestamp(item.stat().st_mtime)
                if (now - dir_time) > timedelta(hours=self.max_age_hours):
                    shutil.rmtree(item)
            except Exception:
                pass

    def get_output_path(self, job_id):
        return self.output_dir / job_id

    def ensure_output_dir(self, job_id):
        path = self.get_output_path(job_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_outputs(self):
        if not self.output_dir.exists():
            return []
        return [d.name for d in self.output_dir.iterdir() if d.is_dir()]
