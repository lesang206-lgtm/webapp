import os
import sys
import secrets
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, session, send_file
from config import *
from key_manager import KeyManager
from mod_runner import ModRunner
from file_manager import FileManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

key_mgr = KeyManager(KEYS_DB)
mod_runner = ModRunner(JOBS_DIR, V7_PY_PATH, KIANA_AOV_DIR)
file_mgr = FileManager(FILE_MOD_DIR)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/request-key', methods=['POST'])
def request_key():
    ip = _get_client_ip()
    key, exp = key_mgr.generate_key(ip)
    key_mgr.save_key(ip, key, exp)

    base_url = f'https://kianamodaov1.blogspot.com/2026/06/webkey.html?ma={key}'
    shortened = key_mgr.shorten_url(base_url, LINK4M_TOKEN)

    return jsonify({'status': 'ok', 'link': shortened or base_url})


@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.get_json(silent=True) or {}
    key = data.get('key', '').strip()
    ip = _get_client_ip()

    if not key:
        return jsonify({'status': 'error', 'message': 'Vui long nhap key!'}), 400

    if key_mgr.validate_key(ip, key):
        session['verified'] = True
        session['ip'] = ip
        session['verified_at'] = datetime.now().isoformat()
        return jsonify({'status': 'ok', 'message': 'Key hop le!'})

    return jsonify({'status': 'error', 'message': 'Key khong hop le!'}), 400


@app.route('/api/check-session')
def check_session():
    ip = _get_client_ip()
    today = datetime.now().strftime('%Y-%m-%d')

    if session.get('verified') and session.get('verified_at', '').startswith(today):
        return jsonify({'status': 'ok', 'verified': True})

    if key_mgr.has_valid_key(ip):
        session['verified'] = True
        session['ip'] = ip
        session['verified_at'] = datetime.now().isoformat()
        return jsonify({'status': 'ok', 'verified': True})

    return jsonify({'status': 'ok', 'verified': False})


@app.route('/api/mod', methods=['POST'])
def create_mod():
    if not session.get('verified'):
        return jsonify({'status': 'error', 'message': 'Vui long xac thuc key truoc!'}), 403

    data = request.get_json(silent=True) or {}
    skin_ids = data.get('skin_ids', [])
    cam_xa = data.get('cam_xa_percent')
    hd_mode = data.get('hd_mode', False)

    if not skin_ids and not cam_xa:
        return jsonify({'status': 'error', 'message': 'Nhap skin ID hoac cam xa!'}), 400

    job_id = mod_runner.create_job(skin_ids, cam_xa, hd_mode)

    t = threading.Thread(target=mod_runner.run_job, args=(job_id,), daemon=True)
    t.start()

    return jsonify({'status': 'ok', 'job_id': job_id})


@app.route('/api/status/<job_id>')
def job_status(job_id):
    job = mod_runner.get_job_status(job_id)
    if not job:
        return jsonify({'status': 'error', 'message': 'Job not found'}), 404

    safe = {
        'status': job['status'],
        'progress': _get_progress(job['status']),
    }
    if job['status'] == 'completed':
        safe['ready'] = True
    elif job['status'] == 'failed':
        safe['message'] = 'Xu ly that bai, vui long thu lai!'

    return jsonify(safe)


@app.route('/api/download/<job_id>')
def download(job_id):
    if not session.get('verified'):
        return jsonify({'status': 'error', 'message': 'Session expired'}), 403

    job = mod_runner.get_job_status(job_id)
    if not job or job['status'] != 'completed':
        return jsonify({'status': 'error', 'message': 'Chua hoan thanh'}), 400

    zip_path = mod_runner.create_download_zip(job_id)
    if zip_path and zip_path.exists():
        return send_file(zip_path, as_attachment=True,
                         download_name=f'mod_{job_id[:8]}.zip')

    return jsonify({'status': 'error', 'message': 'Loi tao file'}), 500


def _get_client_ip():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()
    return ip


def _get_progress(status):
    return {'pending': 10, 'running': 50, 'completed': 100, 'failed': 0}.get(status, 0)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
