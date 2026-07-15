(() => {
    const $ = (id) => document.getElementById(id);

    const authSection = $('auth-section');
    const modSection = $('mod-section');
    const progressSection = $('progress-section');
    const downloadSection = $('download-section');
    const authMsg = $('auth-msg');
    const errorToast = $('error-toast');

    const btnGetKey = $('btn-get-key');
    const btnMod = $('btn-mod');
    const btnDownload = $('btn-download');
    const btnNew = $('btn-new');

    const skinIds = $('skin-ids');
    const camXa = $('cam-xa');
    const hdMode = $('hd-mode');
    const progressFill = $('progress-fill');
    const progressPct = $('progress-pct');
    const progressText = $('progress-text');

    let jobId = null;
    let pollTimer = null;

    checkSession();

    async function checkSession() {
        try {
            const res = await fetch('/api/check-session');
            const data = await res.json();
            if (data.verified) showModSection();
        } catch {}
    }

    btnGetKey.addEventListener('click', async () => {
        setLoading(btnGetKey, true);
        hideMsg(authMsg);

        try {
            const res = await fetch('/api/request-key', { method: 'POST' });
            const data = await res.json();

            if (data.status === 'ok') {
                showMsg(authMsg, 'Da nhan key! Dang chuyen huong...', 'success');
                setTimeout(showModSection, 500);
            } else {
                showMsg(authMsg, data.message || 'Loi lay key', 'error');
            }
        } catch {
            showMsg(authMsg, 'Loi ket noi server', 'error');
        }

        setLoading(btnGetKey, false);
    });

    btnMod.addEventListener('click', async () => {
        const ids = skinIds.value
            .split('\n')
            .map((s) => s.trim())
            .filter((s) => s && /^\d+$/.test(s));
        const cam = camXa.value ? parseInt(camXa.value) : null;
        const hd = hdMode.checked;

        if (!ids.length && !cam) {
            showToast('Nhap skin ID hoac cam xa!');
            return;
        }

        setLoading(btnMod, true);

        try {
            const res = await fetch('/api/mod', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ skin_ids: ids, cam_xa_percent: cam, hd_mode: hd }),
            });
            const data = await res.json();

            if (data.status === 'ok') {
                jobId = data.job_id;
                showProgressSection();
                startPolling();
            } else {
                showToast(data.message || 'Loi tao job');
            }
        } catch {
            showToast('Loi ket noi server');
        }

        setLoading(btnMod, false);
    });

    function startPolling() {
        clearInterval(pollTimer);
        pollTimer = setInterval(fetchStatus, 2000);
        fetchStatus();
    }

    async function fetchStatus() {
        if (!jobId) return;

        try {
            const res = await fetch(`/api/status/${jobId}`);
            const job = await res.json();

            if (job.status === 'completed') {
                clearInterval(pollTimer);
                updateProgress(100, 'Hoan thanh!');
                setTimeout(showDownloadSection, 600);
            } else if (job.status === 'failed') {
                clearInterval(pollTimer);
                showToast(job.message || 'Xu ly that bai');
                resetUI();
            } else {
                updateProgress(job.progress || 50, 'Dang xu ly...');
            }
        } catch {
            clearInterval(pollTimer);
            showToast('Loi kiem tra trang thai');
            resetUI();
        }
    }

    btnDownload.addEventListener('click', () => {
        if (jobId) window.location.href = `/api/download/${jobId}`;
    });

    btnNew.addEventListener('click', () => {
        jobId = null;
        skinIds.value = '';
        camXa.value = '';
        hdMode.checked = false;
        showModSection();
    });

    function showModSection() {
        authSection.classList.add('hidden');
        modSection.classList.remove('hidden');
        progressSection.classList.add('hidden');
        downloadSection.classList.add('hidden');
    }

    function showProgressSection() {
        modSection.classList.add('hidden');
        progressSection.classList.remove('hidden');
        downloadSection.classList.add('hidden');
        updateProgress(10, 'Dang cho xu ly...');
    }

    function showDownloadSection() {
        progressSection.classList.add('hidden');
        downloadSection.classList.remove('hidden');
    }

    function resetUI() {
        progressSection.classList.add('hidden');
        downloadSection.classList.add('hidden');
        modSection.classList.remove('hidden');
    }

    function updateProgress(pct, text) {
        progressFill.style.width = pct + '%';
        progressPct.textContent = pct + '%';
        if (text) progressText.textContent = text;
    }

    function setLoading(btn, loading) {
        const text = btn.querySelector('.btn-text');
        const spin = btn.querySelector('.btn-loading');
        btn.disabled = loading;
        if (text) text.classList.toggle('hidden', loading);
        if (spin) spin.classList.toggle('hidden', !loading);
    }

    function showMsg(el, msg, type) {
        el.textContent = msg;
        el.className = 'msg ' + type;
    }

    function hideMsg(el) {
        el.className = 'msg hidden';
    }

    function showToast(msg) {
        errorToast.textContent = msg;
        errorToast.classList.remove('hidden');
        setTimeout(() => errorToast.classList.add('hidden'), 4000);
    }
})();
