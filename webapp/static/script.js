(() => {
    const $ = (id) => document.getElementById(id);

    const authSection = $('auth-section');
    const modSection = $('mod-section');
    const progressSection = $('progress-section');
    const downloadSection = $('download-section');
    const keyInfo = $('key-info');
    const authMsg = $('auth-msg');
    const errorToast = $('error-toast');

    const btnGetKey = $('btn-get-key');
    const btnVerify = $('btn-verify');
    const btnMod = $('btn-mod');
    const btnDownload = $('btn-download');
    const btnNew = $('btn-new');

    const inputKey = $('input-key');
    const keyLink = $('key-link');
    const skinIds = $('skin-ids');
    const camXa = $('cam-xa');
    const hdMode = $('hd-mode');
    const progressFill = $('progress-fill');
    const progressPct = $('progress-pct');
    const progressText = $('progress-text');

    const skinSearch = $('skin-search');
    const searchResults = $('search-results');
    const selectedTags = $('selected-tags');

    let jobId = null;
    let pollTimer = null;
    let searchTimer = null;
    const selectedSkins = new Map();

    // Theme toggle
    const savedTheme = localStorage.getItem('kiana_theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light');
        $('theme-toggle').innerHTML = '&#9788;';
    }

    window._toggleTheme = function() {
        document.body.classList.toggle('light');
        const isLight = document.body.classList.contains('light');
        $('theme-toggle').innerHTML = isLight ? '&#9788;' : '&#9790;';
        localStorage.setItem('kiana_theme', isLight ? 'light' : 'dark');
    };

    // Subscribe popup
    if (!localStorage.getItem('kiana_subscribed')) {
        $('sub-popup').classList.remove('hidden');
    } else {
        $('sub-popup').classList.add('hidden');
    }

    window._subDone = function() {
        localStorage.setItem('kiana_subscribed', '1');
        const popup = $('sub-popup');
        popup.classList.add('hide');
        setTimeout(() => popup.classList.add('hidden'), 300);
    };

    checkSession();

    async function checkSession() {
        try {
            const res = await fetch('/api/check-session');
            const data = await res.json();
            if (data.verified) showModSection();
        } catch {}
    }

    skinSearch.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(doSearch, 300);
    });

    async function doSearch() {
        const q = skinSearch.value.trim();
        if (!q) { searchResults.innerHTML = ''; return; }
        try {
            const res = await fetch('/api/search?q=' + encodeURIComponent(q));
            const items = await res.json();
            searchResults.innerHTML = items.map(it => {
                const heroPrefix = it.skin_id.substring(0, 3);
                const existing = [...selectedSkins.entries()].find(([sid]) => sid.substring(0, 3) === heroPrefix);
                const alreadySelected = existing ? existing[1] : null;
                return `
                <div class="search-item${alreadySelected ? ' has-skin' : ''}">
                    <div>
                        <div class="search-skin">${it.skin_name}</div>
                        <div class="search-hero">${it.hero} (${it.skin_id})${alreadySelected ? ' - da chon: ' + alreadySelected.split(' - ')[1] : ''}</div>
                    </div>
                    <button class="btn-add" onclick="window._addSkin('${it.skin_id}','${it.hero} - ${it.skin_name}','${heroPrefix}')">${alreadySelected ? 'doi' : '+'}</button>
                </div>`;
            }).join('');
        } catch {}
    }

    window._addSkin = function(id, name, heroPrefix) {
        for (const [sid] of selectedSkins) {
            if (sid.substring(0, 3) === heroPrefix) {
                selectedSkins.delete(sid);
                break;
            }
        }
        selectedSkins.set(id, name);
        renderTags();
        syncTextarea();
        doSearch();
    };

    window._removeSkin = function(id) {
        selectedSkins.delete(id);
        renderTags();
        syncTextarea();
    };

    function renderTags() {
        selectedTags.innerHTML = [...selectedSkins].map(([id, name]) =>
            `<span class="tag">${name} <span class="tag-x" onclick="window._removeSkin('${id}')">&times;</span></span>`
        ).join('');
    }

    function syncTextarea() {
        skinIds.value = [...selectedSkins.keys()].join('\n');
    }

    btnGetKey.addEventListener('click', async () => {
        setLoading(btnGetKey, true);
        hideMsg(authMsg);

        try {
            const res = await fetch('/api/request-key', { method: 'POST' });
            const data = await res.json();

            if (data.status === 'ok') {
                keyLink.href = data.link;
                keyLink.textContent = data.link;
                keyInfo.classList.remove('hidden');
                showMsg(authMsg, 'Da lay link! Bam vao de copy key', 'success');
            } else {
                showMsg(authMsg, data.message || 'Loi lay key', 'error');
            }
        } catch {
            showMsg(authMsg, 'Loi ket noi server', 'error');
        }

        setLoading(btnGetKey, false);
    });

    btnVerify.addEventListener('click', async () => {
        const key = inputKey.value.trim();
        if (!key) {
            showMsg(authMsg, 'Nhap key truoc!', 'error');
            return;
        }

        setLoading(btnVerify, true);
        hideMsg(authMsg);

        try {
            const res = await fetch('/api/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key }),
            });
            const data = await res.json();

            if (data.status === 'ok') {
                showMsg(authMsg, 'Key dung! Moi ban dung tool.', 'success');
                setTimeout(showModSection, 500);
            } else {
                showMsg(authMsg, data.message || 'Key sai!', 'error');
            }
        } catch {
            showMsg(authMsg, 'Loi xac thuc', 'error');
        }

        setLoading(btnVerify, false);
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
        selectedSkins.clear();
        renderTags();
        skinSearch.value = '';
        searchResults.innerHTML = '';
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
