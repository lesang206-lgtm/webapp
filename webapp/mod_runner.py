import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


class ModRunner:
    def __init__(self, jobs_dir, v7_path, kiana_dir):
        self.jobs_dir = Path(jobs_dir)
        self.v7_path = Path(v7_path)
        self.kiana_dir = Path(kiana_dir)
        self.jobs_dir.mkdir(exist_ok=True)

    def create_job(self, skin_ids, cam_xa_percent=None, hd_mode=False):
        job_id = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + os.urandom(4).hex()
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(exist_ok=True)

        list_mod_path = job_dir / 'list_mod.txt'
        with open(list_mod_path, 'w', encoding='utf-8') as f:
            for sid in skin_ids:
                f.write(f'{sid}\n')
            if cam_xa_percent:
                f.write(f'{cam_xa_percent}%\n')

        job_data = {
            'job_id': job_id,
            'status': 'pending',
            'skin_ids': skin_ids,
            'cam_xa_percent': cam_xa_percent,
            'hd_mode': hd_mode,
            'created_at': datetime.now().isoformat(),
            'output_path': None,
            'error': None,
        }

        with open(job_dir / 'job.json', 'w') as f:
            json.dump(job_data, f, indent=2)

        return job_id

    def run_job(self, job_id):
        job_dir = self.jobs_dir / job_id
        job_file = job_dir / 'job.json'

        with open(job_file, 'r') as f:
            job = json.load(f)

        job['status'] = 'running'
        job['started_at'] = datetime.now().isoformat()
        with open(job_file, 'w') as f:
            json.dump(job, f, indent=2)

        try:
            self._run_core(job_dir, job)
            job['status'] = 'completed'
            job['completed_at'] = datetime.now().isoformat()
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
            job['completed_at'] = datetime.now().isoformat()

        with open(job_file, 'w') as f:
            json.dump(job, f, indent=2)

    def _run_core(self, job_dir, job):
        original_cwd = os.getcwd()
        try:
            core_dir = self.v7_path.parent

            res_dir = core_dir / 'KIANA_AOV' / 'Resources'
            if not res_dir.exists():
                raise Exception('Resources not found')

            list_src = job_dir / 'list_mod.txt'
            list_dst = core_dir / 'list_mod.txt'
            shutil.copy2(list_src, list_dst)

            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUNBUFFERED'] = '1'

            hd_input = 'y\n' if job['hd_mode'] else 'n\n'
            folder_name = f"mod_{job['job_id']}"
            output_input = f'{folder_name}\n'
            input_data = (hd_input + output_input).encode('utf-8')

            cmd = [sys.executable, '-u', str(self.v7_path)]
            kwargs = {
                'stdin': subprocess.PIPE,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'env': env,
                'cwd': str(core_dir),
            }

            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                kwargs['startupinfo'] = startupinfo

            process = subprocess.Popen(cmd, **kwargs)
            stdout, stderr = process.communicate(input=input_data, timeout=600)

            if process.returncode != 0:
                stderr_text = stderr.decode('utf-8', errors='replace')
                raise Exception(f'Process failed: {stderr_text[:200]}')

            output_path = core_dir / 'File_mod' / folder_name
            if output_path.exists():
                self._fix_double_nesting(output_path)
                job['output_path'] = str(output_path)
                job['folder_name'] = folder_name
                job['display_name'] = self._make_display_name(output_path, job)
            else:
                raise Exception('Output not found')

        finally:
            os.chdir(original_cwd)
            list_dst = self.v7_path.parent / 'list_mod.txt'
            if list_dst.exists():
                os.remove(list_dst)

    def _fix_double_nesting(self, output_path):
        res_dir = output_path / 'Resources'
        if not res_dir.exists():
            return
        nested_res = res_dir / 'Resources'
        if not nested_res.exists():
            return
        print("  Fixing double Resources nesting...")
        for item in nested_res.iterdir():
            dest = res_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))
        shutil.rmtree(nested_res)

    def _make_display_name(self, output_path, job):
        skin_names = []
        skin_list_file = output_path / 'danhsachskin.txt'
        if skin_list_file.exists():
            with open(skin_list_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split('. ', 1)
                        if len(parts) == 2:
                            skin_names.append(parts[1])
                        else:
                            skin_names.append(line)

        cam = job.get('cam_xa_percent')
        if skin_names:
            count = len(skin_names)
            name = f'pack {count} skin'
            if cam:
                name += f' + cam xa {cam}%'
        elif cam:
            name = f'cam xa {cam}%'
        else:
            name = 'mod'

        return name

    def get_job_status(self, job_id):
        job_file = self.jobs_dir / job_id / 'job.json'
        if not job_file.exists():
            return None
        with open(job_file, 'r') as f:
            return json.load(f)

    def create_download_zip(self, job_id):
        job = self.get_job_status(job_id)
        if not job or job['status'] != 'completed':
            return None

        output_path = Path(job.get('output_path', ''))
        if not output_path.exists():
            return None

        display_name = job.get('display_name', 'mod')
        safe_name = display_name.replace(' ', '_').replace('+', 'n').replace('%', 'pct')
        zip_path = self.jobs_dir / job_id / safe_name
        shutil.make_archive(str(zip_path), 'zip', output_path.parent, output_path.name)
        return zip_path.with_suffix('.zip'), display_name

    def cleanup_old_jobs(self, max_age_hours=24):
        now = datetime.now()
        for job_dir in self.jobs_dir.iterdir():
            if not job_dir.is_dir():
                continue
            job_file = job_dir / 'job.json'
            if not job_file.exists():
                continue
            with open(job_file, 'r') as f:
                job = json.load(f)
            created = datetime.fromisoformat(job['created_at'])
            age = (now - created).total_seconds() / 3600
            if age > max_age_hours:
                shutil.rmtree(job_dir)
