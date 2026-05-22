// === State ===
let state = {
    actors: [],
    currentActor: '',
    currentTags: new Set(),
    currentRating: 0,
    currentStatus: '',
    currentSort: 'time',
    search: '',
    currentMovies: [],
    selected: new Set(),        // selected movie_ids
    viewMode: 'card',          // 'card' | 'table'
    tagEditId: null,
    tagEditTags: [],
};

// === DOM refs ===
const $actorList = document.getElementById('actor-list');
const $actorCount = document.getElementById('actor-count');
const $movieGrid = document.getElementById('movie-grid');
const $movieCount = document.getElementById('movie-count');
const $currentTitle = document.getElementById('current-title');
const $stats = document.getElementById('stats');
const $search = document.getElementById('search');
const $actorSearch = document.getElementById('actor-search');
const $sortSelect = document.getElementById('sort-select');
const $toast = document.getElementById('toast');
const $tagEditor = document.getElementById('tag-editor');
const $tagEditorList = document.getElementById('tag-editor-list');

// === API ===
async function fetchJSON(url, opts = {}) {
    const resp = await fetch(url, opts);
    if (!resp.ok) throw new Error(await resp.text());
    return resp.json();
}

// === Init ===
async function init() {
    const [actors, tagsData, stats] = await Promise.all([
        fetchJSON('/api/actors'),
        fetchJSON('/api/tags'),
        fetchJSON('/api/stats'),
    ]);
    state.actors = actors;
    renderStats(stats);
    renderActorList(actors);
    renderFilterPanel(tagsData);
    await loadMovies();
}

// === Stats ===
function renderStats(stats) {
    $stats.innerHTML = `${stats.total} 部 · ${stats.actors_count} 位演员 · ${stats.classified} 已分类 · ${stats.rated} 已评分 · ${stats.tagged} 有标签`;
}

// === Actor List ===
function renderActorList(actors, filter = '') {
    const searchLower = filter.toLowerCase();
    const filtered = searchLower
        ? actors.filter(a => a.name.toLowerCase().includes(searchLower))
        : actors;

    $actorCount.textContent = `${filtered.length}人`;

    let html = `<div class="actor-item all${!state.currentActor ? ' active' : ''}" onclick="selectActor('')">
        <span class="name">📂 全部影片</span><span class="badge">${actors.reduce((s,a) => s+a.count, 0)}</span>
    </div>`;

    for (const a of filtered) {
        const active = state.currentActor === a.name ? ' active' : '';
        html += `<div class="actor-item${active}" onclick="selectActor('${escAttr(a.name)}')">
            <span class="name">${escHtml(a.name)}</span><span class="badge">${a.count}</span>
        </div>`;
    }

    $actorList.innerHTML = html;
}

// === Filter Panel ===

let tagsDataCache = null;

function renderFilterPanel(tagsData) {
    tagsDataCache = tagsData;
    const usage = tagsData.usage;
    const typeTagSet = new Set(tagsData.type_tags || []);

    // Star filter
    const starFilter = document.getElementById('star-filter');
    if (starFilter) {
        let starHtml = '';
        for (let i = 1; i <= 5; i++) {
            const active = state.currentRating >= i ? ' active' : '';
            starHtml += `<button class="star-btn${active}" onclick="setRatingFilter(${i})">★</button>`;
        }
        if (state.currentRating > 0) {
            starHtml += `<button class="star-btn" onclick="setRatingFilter(0)" style="font-size:0.7rem;color:var(--text2)">✕</button>`;
        }
        starFilter.innerHTML = starHtml;
    }

    // Status chips
    const statusChips = document.getElementById('status-chips');
    if (statusChips) {
        const statuses = [
            { value: '', label: '全部' },
            { value: 'classified', label: '已分类' },
            { value: 'new', label: '未分类' },
        ];
        let chipHtml = '';
        for (const s of statuses) {
            const active = state.currentStatus === s.value ? ' active' : '';
            chipHtml += `<button class="status-chip${active}" onclick="setStatusFilter('${s.value}')">${s.label}</button>`;
        }
        statusChips.innerHTML = chipHtml;
    }

    // Tag grids
    const attrTags = tagsData.all.filter(t => !typeTagSet.has(t) && (usage[t] || 0) > 0);
    const typeTags = [...typeTagSet];

    renderTagGrid('filter-tag-grid-attr', attrTags, usage);
    renderTagGrid('filter-tag-grid-type', typeTags, usage);

    // Update active filter summary
    renderActiveFilters();
}

function renderTagGrid(containerId, tagList, usage) {
    const container = document.getElementById(containerId);
    if (!container) return;
    let html = '';
    for (const tag of tagList) {
        const active = state.currentTags.has(tag) ? ' active' : '';
        const count = usage[tag] || 0;
        html += `<button class="tag-btn${active}" onclick="toggleTag('${escAttr(tag)}')">${escHtml(tag)} ${count}</button>`;
    }
    if (tagList.length === 0) {
        html = '<span style="font-size:0.7rem;color:var(--text2)">暂无标签</span>';
    }
    container.innerHTML = html;
}

function renderActiveFilters() {
    const container = document.getElementById('active-filters');
    const clearBtn = document.getElementById('clear-all-btn');
    const countBadge = document.getElementById('filter-count');
    if (!container) return;

    let count = 0;
    let chips = '';

    if (state.currentRating > 0) {
        count++;
        chips += `<span class="active-filter-chip">⭐ ≥${state.currentRating}<span class="remove" onclick="setRatingFilter(0)">✕</span></span>`;
    }
    if (state.currentStatus) {
        count++;
        const label = state.currentStatus === 'classified' ? '已分类' : '未分类';
        chips += `<span class="active-filter-chip">📌 ${label}<span class="remove" onclick="setStatusFilter('')">✕</span></span>`;
    }
    for (const tag of state.currentTags) {
        count++;
        chips += `<span class="active-filter-chip">🏷 ${escHtml(tag)}<span class="remove" onclick="removeFilter('tag', '${escAttr(tag)}')">✕</span></span>`;
    }

    container.innerHTML = chips;
    clearBtn.style.display = count > 0 ? '' : 'none';
    countBadge.style.display = count > 0 ? '' : 'none';
    if (count > 0) countBadge.textContent = count;
}

function toggleFilterPanel() {
    const panel = document.getElementById('filter-panel');
    const toggle = document.getElementById('filter-toggle');
    if (!panel || !toggle) return;
    const isOpen = panel.style.display !== 'none';
    panel.style.display = isOpen ? 'none' : 'flex';
    toggle.innerHTML = isOpen
        ? '🔽 筛选条件<span class="filter-count" id="filter-count" style="display:none"></span>'
        : '🔼 收起筛选<span class="filter-count" id="filter-count" style="display:none"></span>';
    // Re-render count badge
    const count = (state.currentRating > 0 ? 1 : 0) + (state.currentStatus ? 1 : 0) + state.currentTags.size;
    if (count > 0) {
        const badge = toggle.querySelector('.filter-count');
        if (badge) { badge.style.display = ''; badge.textContent = count; }
    }
}

function setRatingFilter(rating) {
    state.currentRating = rating;
    if (tagsDataCache) renderFilterPanel(tagsDataCache);
    loadMovies();
}

function setStatusFilter(status) {
    state.currentStatus = status;
    if (tagsDataCache) renderFilterPanel(tagsDataCache);
    loadMovies();
}

function removeFilter(type, value) {
    if (type === 'tag') {
        state.currentTags.delete(value);
    } else if (type === 'rating') {
        state.currentRating = 0;
    } else if (type === 'status') {
        state.currentStatus = '';
    }
    // Refresh from cached tags data
    fetchJSON('/api/tags').then(renderFilterPanel);
    loadMovies();
}

function clearAllFilters() {
    state.currentTags.clear();
    state.currentRating = 0;
    state.currentStatus = '';
    if (tagsDataCache) renderFilterPanel(tagsDataCache);
    loadMovies();
}

function toggleTag(tag) {
    if (state.currentTags.has(tag)) {
        state.currentTags.delete(tag);
    } else {
        state.currentTags.add(tag);
    }
    if (tagsDataCache) renderFilterPanel(tagsDataCache);
    loadMovies();
}

// === Actor Selection ===
function selectActor(name) {
    state.currentActor = name;
    renderActorList(state.actors, $actorSearch.value);
    $currentTitle.textContent = name || '全部影片';
    loadMovies();
}

// === Load Movies ===
let loadTimer = null;
async function loadMovies() {
    clearTimeout(loadTimer);
    loadTimer = setTimeout(async () => {
        const params = new URLSearchParams();
        if (state.currentActor) params.set('actor', state.currentActor);
        if (state.currentTags.size > 0) params.set('tags', [...state.currentTags].join(','));
        if (state.currentRating > 0) params.set('rating_min', state.currentRating);
        if (state.currentStatus) params.set('status', state.currentStatus);
        if (state.search) params.set('search', state.search);
        params.set('sort', state.currentSort);

        const movies = await fetchJSON(`/api/movies?${params}`);
        state.currentMovies = movies;
        renderMovies(movies);
    }, 150);
}

// === Render Movies (dispatches to card or table view) ===
function renderMovies(movies) {
    $movieCount.textContent = `${movies.length} 部`;

    if (movies.length === 0) {
        $movieGrid.innerHTML = `<div class="empty"><div class="icon">📭</div><p>没有找到匹配的影片</p></div>`;
        $movieGrid.style.display = '';
        document.getElementById('movie-table-wrap').style.display = 'none';
        return;
    }

    if (state.viewMode === 'table') {
        renderTable(movies);
    } else {
        renderCards(movies);
    }
}

// === Card View ===
function renderCards(movies) {
    document.getElementById('movie-table-wrap').style.display = 'none';
    $movieGrid.style.display = '';

    let html = '';
    for (const m of movies) {
        const year = m.release_year || '-';
        const size = m.file_size || '-';
        const checked = state.selected.has(m.movie_id) ? ' checked' : '';
        const ratedClass = m.rating >= 4 ? ' rated-high' : (m.rating >= 1 ? ' rated' : '');

        let starsHtml = '<span class="stars">';
        for (let i = 1; i <= 5; i++) {
            const cls = i <= m.rating ? 'active' : 'inactive';
            starsHtml += `<span class="star ${cls}" onclick="setRating('${escAttr(m.movie_id)}', ${i})">★</span>`;
        }
        starsHtml += '</span>';

        let tagsHtml = '';
        if (m.tags.length > 0) {
            for (const t of m.tags) {
                const hl = state.currentTags.has(t) ? ' highlight' : '';
                tagsHtml += `<span class="tag${hl}">${escHtml(t)}</span>`;
            }
        }
        tagsHtml += `<span class="tag-add-btn" onclick="openTagEditor('${escAttr(m.movie_id)}', '${escAttr(m.tags.join(','))}')">+</span>`;

        const actorLine = !state.currentActor && m.actor
            ? `<div class="actor-name">${escHtml(m.actor)}</div>`
            : '';

        html += `
        <div class="movie-card${ratedClass}">
            <input type="checkbox" class="card-checkbox"${checked} onchange="toggleSelect('${escAttr(m.movie_id)}', this.checked)" onclick="event.stopPropagation()">
            <div class="code" onclick="playMovie('${escAttr(m.movie_id)}')" title="点击播放" style="cursor:pointer">${escHtml(m.movie_name)}</div>
            ${actorLine}
            ${starsHtml}
            <div class="meta">
                <span>${year}</span>
                <span>${size}</span>
            </div>
            <div class="tags-row">${tagsHtml}</div>
            <div class="card-bottom">
                <span class="time">${m.downloaded_at ? m.downloaded_at.slice(0, 10) : ''}</span>
                <span class="folder-btn" onclick="openFolder('${escAttr(m.movie_id)}')" title="在资源管理器中打开">📂</span>
            </div>
        </div>`;
    }

    $movieGrid.innerHTML = html;
}

// === Table View ===
function renderTable(movies) {
    $movieGrid.style.display = 'none';
    document.getElementById('movie-table-wrap').style.display = '';

    let html = '';
    for (const m of movies) {
        const year = m.release_year || '-';
        const size = m.file_size || '-';
        const checked = state.selected.has(m.movie_id) ? ' checked' : '';
        const time = m.downloaded_at ? m.downloaded_at.slice(0, 10) : '';

        let starsHtml = '<span class="table-stars">';
        for (let i = 1; i <= 5; i++) {
            const cls = i <= m.rating ? 'active' : 'inactive';
            starsHtml += `<span class="star ${cls}" onclick="setRating('${escAttr(m.movie_id)}', ${i}); event.stopPropagation();">★</span>`;
        }
        starsHtml += '</span>';

        let tagsHtml = '';
        if (m.tags.length > 0) {
            for (const t of m.tags) {
                const hl = state.currentTags.has(t) ? ' highlight' : '';
                tagsHtml += `<span class="table-tag${hl}">${escHtml(t)}</span>`;
            }
        }
        tagsHtml += `<span class="table-tag-add" onclick="openTagEditor('${escAttr(m.movie_id)}', '${escAttr(m.tags.join(','))}'); event.stopPropagation();">+</span>`;

        html += `<tr>
            <td><input type="checkbox"${checked} onchange="toggleSelect('${escAttr(m.movie_id)}', this.checked); event.stopPropagation();"></td>
            <td><span class="code-link" onclick="playMovie('${escAttr(m.movie_id)}')" title="点击播放">${escHtml(m.movie_name)}</span></td>
            <td>${escHtml(m.actor || '-')}</td>
            <td>${year}</td>
            <td>${starsHtml}</td>
            <td>${tagsHtml}</td>
            <td>${size}</td>
            <td>${time}</td>
            <td>
                <button class="action-btn play-btn" onclick="playMovie('${escAttr(m.movie_id)}')" title="播放">▶️</button>
                <button class="action-btn" onclick="openFolder('${escAttr(m.movie_id)}')" title="打开位置">📂</button>
            </td>
        </tr>`;
    }

    document.getElementById('movie-tbody').innerHTML = html;
    document.getElementById('select-all-checkbox').checked = false;
}

// === View Switch ===
function switchView(mode) {
    state.viewMode = mode;
    document.querySelectorAll('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === mode));
    renderMovies(state.currentMovies);
}

// === Rating ===
async function setRating(movieId, rating) {
    try {
        await fetchJSON(`/api/movies/${movieId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rating }),
        });
        showToast(`评分已更新: ${'★'.repeat(rating)}`);
        await loadMoviesSilent();
        fetchJSON('/api/tags').then(renderFilterPanel);
        fetchJSON('/api/stats').then(renderStats);
    } catch (e) {
        showToast('评分失败: ' + e.message, true);
    }
}

// === Tag Editor ===
async function openTagEditor(movieId, currentTagsStr) {
    state.tagEditId = movieId;
    state.tagEditTags = currentTagsStr ? currentTagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];

    const tagsData = await fetchJSON('/api/tags');
    // Editor shows: predefined tags (always) + custom tags with usage + tags already on this movie
    const allShown = new Set(tagsData.predefined);
    for (const t of tagsData.all) {
        if ((tagsData.usage[t] || 0) > 0) allShown.add(t);
    }
    for (const t of state.tagEditTags) allShown.add(t);
    let html = '';
    for (const tag of allShown) {
        const selected = state.tagEditTags.includes(tag) ? ' selected' : '';
        html += `<span class="tag-chip${selected}" onclick="toggleTagChip(this, '${escAttr(tag)}')">${escHtml(tag)}</span>`;
    }
    $tagEditorList.innerHTML = html;
    document.getElementById('tag-custom-input').value = '';
    // Reset "add to library" state
    document.getElementById('add-to-lib-check')?.remove();
    $tagEditor.style.display = 'block';
}

function toggleTagChip(el, tag) {
    const idx = state.tagEditTags.indexOf(tag);
    if (idx >= 0) {
        state.tagEditTags.splice(idx, 1);
        el.classList.remove('selected');
    } else {
        state.tagEditTags.push(tag);
        el.classList.add('selected');
    }
}

function addCustomTag() {
    const input = document.getElementById('tag-custom-input');
    const tag = input.value.trim();
    if (!tag) return;
    if (!state.tagEditTags.includes(tag)) {
        state.tagEditTags.push(tag);
        const chip = document.createElement('span');
        chip.className = 'tag-chip selected';
        chip.textContent = tag;
        chip.onclick = () => toggleTagChip(chip, tag);
        $tagEditorList.appendChild(chip);
    }
    input.value = '';

    // Show "add to library" checkbox if tag is not in predefined list
    showAddToLib(tag);
}

async function showAddToLib(tag) {
    const tagsData = await fetchJSON('/api/tags');
    if (!tagsData.predefined.includes(tag)) {
        // Remove old checkbox if exists
        document.getElementById('add-to-lib-check')?.remove();
        const div = document.createElement('div');
        div.id = 'add-to-lib-check';
        div.style.cssText = 'margin-top:8px;font-size:0.8rem;color:var(--text2)';
        div.innerHTML = `<label style="cursor:pointer;display:flex;align-items:center;gap:6px">
            <input type="checkbox" id="add-to-lib"> 将「${escHtml(tag)}」添加到标签库（可在筛选栏使用）
        </label>`;
        $tagEditorList.after(div);
    }
}

async function saveTags() {
    if (!state.tagEditId) return;
    const tagsStr = state.tagEditTags.join(',');

    // Check if "add to library" is checked
    const addToLib = document.getElementById('add-to-lib');
    if (addToLib && addToLib.checked) {
        // Add each new tag to the library
        const tagsData = await fetchJSON('/api/tags');
        for (const t of state.tagEditTags) {
            if (!tagsData.predefined.includes(t)) {
                await fetchJSON('/api/tags/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tag: t }),
                });
            }
        }
    }

    try {
        await fetchJSON(`/api/movies/${state.tagEditId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tags: tagsStr }),
        });
        closeTagEditor();
        showToast('标签已保存');
        await loadMovies();
        fetchJSON('/api/tags').then(renderFilterPanel);
        fetchJSON('/api/stats').then(renderStats);
    } catch (e) {
        showToast('保存失败: ' + e.message, true);
    }
}

function closeTagEditor() {
    $tagEditor.style.display = 'none';
    state.tagEditId = null;
    state.tagEditTags = [];
}

// === Export CSV ===
function exportCSV() {
    const params = new URLSearchParams();
    if (state.currentActor) params.set('actor', state.currentActor);
    if (state.currentTags.size > 0) params.set('tags', [...state.currentTags].join(','));
    if (state.currentRating > 0) params.set('rating_min', state.currentRating);
    if (state.currentStatus) params.set('status', state.currentStatus);
    if (state.search) params.set('search', state.search);
    window.open(`/api/movies/export?${params}`, '_blank');
    showToast('正在导出...');
}

// === Open in Explorer ===
async function openFolder(movieId) {
    try {
        await fetchJSON('/api/open-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ movie_id: movieId }),
        });
    } catch (e) {
        showToast('打开失败: ' + e.message, true);
    }
}

// === Open filtered in Explorer ===
async function openFiltered() {
    const body = {
        actor: state.currentActor,
        tags: [...state.currentTags].join(','),
        rating_min: state.currentRating,
        status: state.currentStatus,
        search: state.search,
    };
    // If user selected specific movies, only open those
    if (state.selected.size > 0) {
        body.ids = [...state.selected];
    }
    try {
        const r = await fetchJSON('/api/open-filtered', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        showToast(`已打开筛选结果: ${r.files} 个文件 → E:\\筛选结果`);
    } catch (e) {
        showToast('打开失败: ' + e.message, true);
    }
}

// === Selection ===
function toggleSelect(id, checked) {
    if (checked) state.selected.add(id);
    else state.selected.delete(id);
    updateSelectedInfo();
}

function selectAllVisible() {
    for (const m of state.currentMovies) state.selected.add(m.movie_id);
    document.querySelectorAll('.card-checkbox, #movie-tbody input[type=checkbox]').forEach(cb => { cb.checked = true; });
    document.getElementById('select-all-checkbox') && (document.getElementById('select-all-checkbox').checked = true);
    updateSelectedInfo();
}

function deselectAll() {
    state.selected.clear();
    document.querySelectorAll('.card-checkbox, #movie-tbody input[type=checkbox]').forEach(cb => { cb.checked = false; });
    document.getElementById('select-all-checkbox') && (document.getElementById('select-all-checkbox').checked = false);
    updateSelectedInfo();
}

function toggleAll(checked) {
    if (checked) {
        for (const m of state.currentMovies) state.selected.add(m.movie_id);
    } else {
        for (const m of state.currentMovies) state.selected.delete(m.movie_id);
    }
    document.querySelectorAll('#movie-tbody input[type=checkbox]').forEach(cb => { cb.checked = checked; });
    updateSelectedInfo();
}

function updateSelectedInfo() {
    const info = document.getElementById('selected-info');
    const batchBtns = document.getElementById('batch-btns');
    const count = state.selected.size;
    if (count > 0) {
        info.style.display = 'inline';
        info.textContent = `已选 ${count}`;
        batchBtns.style.display = 'inline';
    } else {
        info.style.display = 'none';
        batchBtns.style.display = 'none';
    }
}

// === Silent reload ===
async function loadMoviesSilent() {
    const params = new URLSearchParams();
    if (state.currentActor) params.set('actor', state.currentActor);
    if (state.currentTags.size > 0) params.set('tags', [...state.currentTags].join(','));
    if (state.currentRating > 0) params.set('rating_min', state.currentRating);
    if (state.currentStatus) params.set('status', state.currentStatus);
    if (state.search) params.set('search', state.search);
    params.set('sort', state.currentSort);
    const movies = await fetchJSON(`/api/movies?${params}`);
    state.currentMovies = movies;
    renderMovies(movies);
}

// === Play Video ===
async function playMovie(movieId) {
    try {
        await fetchJSON(`/api/play/${movieId}`, { method: 'POST' });
        showToast('正在播放...');
    } catch (e) {
        showToast('播放失败: ' + e.message, true);
    }
}

// === Batch Operations ===
function showDestDialog(title, onConfirm) {
    // Remove existing dialog
    document.querySelector('.dialog-overlay')?.remove();

    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `<div class="dialog-box">
        <h3>${title}</h3>
        <p>目标路径 (WSL格式, 如 /mnt/e/目标文件夹):</p>
        <input type="text" class="dest-input" id="dest-input" placeholder="/mnt/e/..." autocomplete="off">
        <div class="dialog-actions">
            <button class="btn-cancel" id="dialog-cancel">取消</button>
            <button class="btn-confirm" id="dialog-confirm">确认</button>
        </div>
    </div>`;

    document.body.appendChild(overlay);

    const input = overlay.querySelector('#dest-input');
    input.focus();
    overlay.querySelector('#dialog-cancel').onclick = () => overlay.remove();
    overlay.querySelector('#dialog-confirm').onclick = () => {
        const dest = input.value.trim();
        if (!dest) {
            showToast('请输入目标路径', true);
            return;
        }
        overlay.remove();
        onConfirm(dest);
    };
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
}

function showConfirmDialog(title, message, onConfirm) {
    document.querySelector('.dialog-overlay')?.remove();

    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `<div class="dialog-box">
        <h3>${title}</h3>
        <p>${message}</p>
        <div class="dialog-actions">
            <button class="btn-cancel" id="dialog-cancel">取消</button>
            <button class="btn-danger" id="dialog-confirm">确认删除</button>
        </div>
    </div>`;

    document.body.appendChild(overlay);
    overlay.querySelector('#dialog-cancel').onclick = () => overlay.remove();
    overlay.querySelector('#dialog-confirm').onclick = () => {
        overlay.remove();
        onConfirm();
    };
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
}

async function batchDelete() {
    const ids = [...state.selected];
    if (ids.length === 0) {
        showToast('请先选择影片', true);
        return;
    }
    showConfirmDialog('确认删除', `确定要删除选中的 ${ids.length} 部影片？<br><br>⚠️ 此操作将同时删除文件和 Excel 记录，不可撤销！`, async () => {
        try {
            const r = await fetchJSON('/api/movies/batch/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids }),
            });
            state.selected.clear();
            updateSelectedInfo();
            showToast(`已删除 ${r.deleted_files} 个文件`);
            await loadMovies();
            fetchJSON('/api/tags').then(renderFilterPanel);
            fetchJSON('/api/stats').then(renderStats);
        } catch (e) {
            showToast('删除失败: ' + e.message, true);
        }
    });
}

async function batchMove() {
    const ids = [...state.selected];
    if (ids.length === 0) {
        showToast('请先选择影片', true);
        return;
    }
    showDestDialog('移动影片', async (dest) => {
        try {
            const r = await fetchJSON('/api/movies/batch/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids, dest }),
            });
            state.selected.clear();
            updateSelectedInfo();
            showToast(`已移动 ${r.moved} 部影片`);
            await loadMovies();
            fetchJSON('/api/tags').then(renderFilterPanel);
            fetchJSON('/api/stats').then(renderStats);
        } catch (e) {
            showToast('移动失败: ' + e.message, true);
        }
    });
}

async function batchCopy() {
    const ids = [...state.selected];
    if (ids.length === 0) {
        showToast('请先选择影片', true);
        return;
    }
    showDestDialog('复制影片', async (dest) => {
        try {
            const r = await fetchJSON('/api/movies/batch/copy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids, dest }),
            });
            state.selected.clear();
            updateSelectedInfo();
            showToast(`已复制 ${r.copied} 部影片`);
        } catch (e) {
            showToast('复制失败: ' + e.message, true);
        }
    });
}

// === Batch Tag Operations ===
function showTagBatchDialog(title, mode, onConfirm) {
    document.querySelector('.dialog-overlay')?.remove();

    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `<div class="dialog-box" style="min-width:400px">
        <h3>${title}</h3>
        <p style="font-size:0.8rem;color:var(--text2);margin-bottom:10px">
            已选 ${state.selected.size} 部影片 · 点击标签选择 / 取消选择
        </p>
        <div class="tag-editor-list" id="batch-tag-list"></div>
        <div class="batch-tag-templates" id="batch-tag-templates" style="margin-top:8px">
            <span style="font-size:0.75rem;color:var(--text2);margin-right:6px">模板:</span>
        </div>
        <div class="tag-editor-custom" style="margin-top:10px">
            <input type="text" id="batch-tag-custom" placeholder="自定义标签...">
            <button onclick="addBatchCustomTag()">+</button>
        </div>
        <div class="dialog-actions" style="margin-top:14px">
            <button class="btn-cancel" id="batch-tag-cancel">取消</button>
            <button class="btn-confirm" id="batch-tag-confirm">确认</button>
        </div>
    </div>`;

    document.body.appendChild(overlay);

    // Populate tag chips
    fetchJSON('/api/tags').then(tagsData => {
        const allShown = new Set(tagsData.predefined);
        for (const t of tagsData.all) {
            if ((tagsData.usage[t] || 0) > 0) allShown.add(t);
        }
        const selectedTags = new Set();
        const list = overlay.querySelector('#batch-tag-list');
        let chipHtml = '';
        for (const tag of allShown) {
            chipHtml += `<span class="tag-chip" data-tag="${escAttr(tag)}" onclick="this.classList.toggle('selected');event.stopPropagation();">${escHtml(tag)}</span>`;
        }
        list.innerHTML = chipHtml;
    });

    // Populate tag templates
    fetchJSON('/api/tag-templates').then(templates => {
        const tmplDiv = overlay.querySelector('#batch-tag-templates');
        if (!templates || Object.keys(templates).length === 0) {
            tmplDiv.style.display = 'none';
            return;
        }
        let btnHtml = '';
        for (const [name, tags] of Object.entries(templates)) {
            btnHtml += `<button class="tmpl-btn" data-tmpl-tags="${escAttr(tags.join(','))}"
                title="${escAttr(tags.join(', '))}"
                onclick="applyTemplate(this)">${escHtml(name)}</button>`;
        }
        tmplDiv.innerHTML += btnHtml;
    });

    overlay.querySelector('#batch-tag-cancel').onclick = () => overlay.remove();
    overlay.querySelector('#batch-tag-confirm').onclick = () => {
        const chips = overlay.querySelectorAll('.tag-chip.selected');
        const tags = [...chips].map(c => c.dataset.tag);
        overlay.remove();
        onConfirm(tags);
    };
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
}

function addBatchCustomTag() {
    const input = document.getElementById('batch-tag-custom');
    const tag = input.value.trim();
    if (!tag) return;
    const list = document.getElementById('batch-tag-list');
    const chip = document.createElement('span');
    chip.className = 'tag-chip selected';
    chip.dataset.tag = tag;
    chip.textContent = tag;
    chip.onclick = function() { this.classList.toggle('selected'); event.stopPropagation(); };
    list.appendChild(chip);
    input.value = '';
}

function applyTemplate(btn) {
    const tags = btn.dataset.tmplTags.split(',');
    const list = document.getElementById('batch-tag-list');
    if (!list) return;
    // Select matching chips, deselect others
    const chips = list.querySelectorAll('.tag-chip');
    for (const chip of chips) {
        if (tags.includes(chip.dataset.tag)) {
            chip.classList.add('selected');
        } else {
            chip.classList.remove('selected');
        }
    }
}

async function batchTagsAdd() {
    if (state.selected.size === 0) {
        showToast('请先选择影片', true);
        return;
    }
    showTagBatchDialog('批量添加标签', 'add', async (tags) => {
        if (tags.length === 0) {
            showToast('请选择至少一个标签', true);
            return;
        }
        try {
            const r = await fetchJSON('/api/movies/batch/tags/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: [...state.selected], tags }),
            });
            showToast(`已为 ${r.updated} 部影片添加标签: ${r.added.join(', ')}`);
            await loadMovies();
            fetchJSON('/api/tags').then(renderFilterPanel);
            fetchJSON('/api/stats').then(renderStats);
        } catch (e) {
            showToast('添加失败: ' + e.message, true);
        }
    });
}

async function batchTagsSet() {
    if (state.selected.size === 0) {
        showToast('请先选择影片', true);
        return;
    }
    showTagBatchDialog('批量修改标签（覆盖）', 'set', async (tags) => {
        try {
            const r = await fetchJSON('/api/movies/batch/tags/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: [...state.selected], tags }),
            });
            showToast(`已覆盖 ${r.updated} 部影片的标签: ${r.tags || '（清空）'}`);
            await loadMovies();
            fetchJSON('/api/tags').then(renderFilterPanel);
            fetchJSON('/api/stats').then(renderStats);
        } catch (e) {
            showToast('修改失败: ' + e.message, true);
        }
    });
}

async function batchTagsRemove() {
    if (state.selected.size === 0) {
        showToast('请先选择影片', true);
        return;
    }
    showTagBatchDialog('批量移除标签', 'remove', async (tags) => {
        if (tags.length === 0) {
            showToast('请选择至少一个要移除的标签', true);
            return;
        }
        try {
            const r = await fetchJSON('/api/movies/batch/tags/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: [...state.selected], tags }),
            });
            showToast(`已从 ${r.updated} 部影片移除标签: ${r.removed.join(', ')}`);
            await loadMovies();
            fetchJSON('/api/tags').then(renderFilterPanel);
            fetchJSON('/api/stats').then(renderStats);
        } catch (e) {
            showToast('移除失败: ' + e.message, true);
        }
    });
}

// === Tag Manager ===
async function openTagManager() {
    document.querySelector('.dialog-overlay')?.remove();

    const tagsData = await fetchJSON('/api/tags');

    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `<div class="dialog-box" style="min-width:500px;max-width:620px">
        <h3>🏷 标签管理</h3>
        <div style="margin-bottom:8px;display:flex;gap:6px;align-items:center">
            <input type="text" id="tagmgr-new-input" placeholder="新标签名..." style="flex:1;padding:6px 10px;background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);color:var(--text);font-size:0.85rem;outline:none">
            <select id="tagmgr-group" style="padding:6px 8px;background:var(--bg3);border:1px solid var(--border);color:var(--text);border-radius:var(--radius);font-size:0.8rem">
                <option value="attribute">属性标签</option>
                <option value="type">类型标签</option>
            </select>
            <button class="dialog-actions btn-confirm" id="tagmgr-add-btn" style="padding:6px 14px;font-size:0.85rem;white-space:nowrap">＋ 添加</button>
        </div>
        <div id="tagmgr-list" style="max-height:340px;overflow-y:auto">
            <div style="font-size:0.75rem;color:var(--accent2);padding:6px 0 4px;border-bottom:1px solid var(--border);margin-bottom:4px">📌 属性标签</div>
            <table style="width:100%;border-collapse:collapse;font-size:0.82rem;margin-bottom:12px">
                <tbody id="tagmgr-tbody-attr"></tbody>
            </table>
            <div style="font-size:0.75rem;color:var(--accent2);padding:6px 0 4px;border-bottom:1px solid var(--border);margin-bottom:4px">🎬 类型标签</div>
            <table style="width:100%;border-collapse:collapse;font-size:0.82rem">
                <tbody id="tagmgr-tbody-type"></tbody>
            </table>
        </div>
        <div class="dialog-actions" style="margin-top:10px">
            <button class="btn-cancel" id="tagmgr-close">关闭</button>
        </div>
    </div>`;

    document.body.appendChild(overlay);
    overlay.querySelector('#tagmgr-close').onclick = () => overlay.remove();
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });

    renderTagListGrouped(overlay, tagsData);

    overlay.querySelector('#tagmgr-add-btn').onclick = async () => {
        const input = overlay.querySelector('#tagmgr-new-input');
        const group = overlay.querySelector('#tagmgr-group').value;
        const name = input.value.trim();
        if (!name) return;
        try {
            await fetchJSON('/api/tags/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag: name, group }),
            });
            input.value = '';
            const fresh = await fetchJSON('/api/tags');
            Object.assign(tagsData, fresh);
            renderTagListGrouped(overlay, tagsData);
            renderFilterPanel(fresh);
            showToast(`已添加${group === 'type' ? '类型' : '属性'}标签: ${name}`);
        } catch (e) {
            showToast('添加失败: ' + e.message, true);
        }
    };
}

function renderTagListGrouped(overlay, tagsData) {
    const typeSet = new Set(tagsData.type_tags || []);
    const allTags = tagsData.all;
    const usage = tagsData.usage;

    const attrTags = allTags.filter(t => !typeSet.has(t));
    const typeTagsList = allTags.filter(t => typeSet.has(t));

    renderTagGroupBody(overlay, 'tagmgr-tbody-attr', attrTags, usage, tagsData, false);
    renderTagGroupBody(overlay, 'tagmgr-tbody-type', typeTagsList, usage, tagsData, true);
}

function renderTagGroupBody(overlay, tbodyId, tags, usage, tagsData, isType) {
    const tbody = overlay.querySelector('#' + tbodyId);
    if (!tbody) return;
    let html = '';
    for (const tag of tags) {
        const count = usage[tag] || 0;
        html += `<tr>
            <td style="padding:4px 8px;border-bottom:1px solid var(--border)">${escHtml(tag)}</td>
            <td style="text-align:right;padding:4px 8px;border-bottom:1px solid var(--border);color:var(--text2);width:50px">${count}</td>
            <td style="text-align:center;padding:4px;border-bottom:1px solid var(--border);width:70px;white-space:nowrap">
                <button class="batch-btn" style="font-size:0.65rem;padding:2px 6px" data-rename="${escAttr(tag)}">✎</button>
                <button class="batch-btn delete-btn" style="font-size:0.65rem;padding:2px 6px" data-delete="${escAttr(tag)}">✕</button>
            </td>
        </tr>`;
    }
    if (!tags.length) {
        html = `<tr><td colspan="3" style="padding:6px 8px;font-size:0.7rem;color:var(--text2)">${isType ? '暂无类型标签，在上方添加' : '暂无属性标签'}</td></tr>`;
    }
    tbody.innerHTML = html;

    tbody.querySelectorAll('[data-rename]').forEach(btn => {
        btn.onclick = () => {
            const oldTag = btn.dataset.rename;
            const newName = prompt(`重命名「${oldTag}」为:`, oldTag);
            if (!newName || newName.trim() === oldTag) return;
            renameTagAndRefresh(overlay, tagsData, oldTag, newName.trim());
        };
    });
    tbody.querySelectorAll('[data-delete]').forEach(btn => {
        btn.onclick = () => {
            const tag = btn.dataset.delete;
            const count = usage[tag] || 0;
            deleteTagAndRefresh(overlay, tagsData, tag, count > 0);
        };
    });
}

async function renameTagAndRefresh(overlay, tagsData, oldName, newName) {
    try {
        await fetchJSON(`/api/tags/${encodeURIComponent(oldName)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName }),
        });
        const fresh = await fetchJSON('/api/tags');
        Object.assign(tagsData, fresh);
        // Re-render the list in-place
        renderTagListGrouped(overlay, tagsData);
        await loadMovies();
        renderFilterPanel(fresh);
        fetchJSON('/api/stats').then(renderStats);
        showToast(`已重命名: ${oldName} → ${newName}`);
    } catch (e) {
        showToast('重命名失败: ' + e.message, true);
    }
}

async function deleteTagAndRefresh(overlay, tagsData, tag, cleanMovies) {
    try {
        await fetchJSON(`/api/tags/${encodeURIComponent(tag)}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clean_movies: cleanMovies }),
        });
        const fresh = await fetchJSON('/api/tags');
        Object.assign(tagsData, fresh);
        renderTagListGrouped(overlay, tagsData);
        await loadMovies();
        renderFilterPanel(fresh);
        fetchJSON('/api/stats').then(renderStats);
        showToast(`已删除标签: ${tag}`);
    } catch (e) {
        showToast('删除失败: ' + e.message, true);
    }
}

// === Toast ===
let toastTimer = null;
function showToast(msg, isError = false) {
    clearTimeout(toastTimer);
    $toast.textContent = msg;
    $toast.className = 'toast show' + (isError ? ' error' : '');
    toastTimer = setTimeout(() => { $toast.className = 'toast'; }, 2800);
}

// === Keyboard ===
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        if (e.key === 'Escape') e.target.blur();
        return;
    }
    if (e.key === 'Escape') closeTagEditor();
});

// === Event Listeners ===
$search.addEventListener('input', () => {
    state.search = $search.value.trim();
    loadMovies();
});

$actorSearch.addEventListener('input', () => {
    renderActorList(state.actors, $actorSearch.value);
});

$sortSelect.addEventListener('change', () => {
    state.currentSort = $sortSelect.value;
    loadMovies();
});

// Rating and status filters now handled via filter panel UI (setRatingFilter, setStatusFilter)

// === Helpers ===
function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function escAttr(s) {
    return s.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// === Init ===
init();
