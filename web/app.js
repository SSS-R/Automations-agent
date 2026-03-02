document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // State
    let videos = [];
    let currentVideoId = null;

    // DOM Elements
    const videoListEl = document.getElementById('video-list');
    const clipsGridEl = document.getElementById('clips-grid');
    const headerTitleEl = document.getElementById('current-video-title');
    const headerStatsEl = document.getElementById('current-video-stats');
    const toastEl = document.getElementById('toast');

    // Phase 3 Elements
    const processBtn = document.getElementById('process-btn');
    const urlInput = document.getElementById('video-url-input');
    const progressContainer = document.getElementById('progress-container');
    const progressStatus = document.getElementById('progress-status');
    const progressBarFill = document.getElementById('progress-bar-fill');

    // Fetch initial data
    async function fetchVideos() {
        try {
            const response = await fetch('/api/videos');
            videos = await response.json();
            renderVideoList();

            if (videos.length > 0) {
                selectVideo(videos[0].id);
            } else {
                showEmptyState("No processed videos found yet. Run the pipeline first!");
            }
        } catch (error) {
            console.error("Failed to fetch videos:", error);
            showEmptyState("Failed to connect to the backend API.");
        }
    }

    // Process new video
    processBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) return;

        urlInput.disabled = true;
        processBtn.disabled = true;

        try {
            const res = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await res.json();

            if (data.task_id) {
                pollProgress(data.task_id);
            }
        } catch (error) {
            console.error(error);
            showToast("Failed to start processing");
            resetProcessForm();
        }
    });

    function pollProgress(taskId) {
        progressContainer.classList.remove('hidden');
        progressStatus.textContent = "Starting Pipeline...";
        progressBarFill.style.width = '0%';

        const intervalId = setInterval(async () => {
            try {
                const res = await fetch(`/api/status/${taskId}`);
                const data = await res.json();

                progressBarFill.style.width = `${data.progress}%`;
                progressStatus.textContent = `${data.progress}% - ${data.status}`;

                if (data.state === 'SUCCESS') {
                    clearInterval(intervalId);
                    showToast("Pipeline Complete!");
                    resetProcessForm();
                    fetchVideos(); // Refresh sidebar with new video
                    fetchStats();  // Refresh analytics
                } else if (data.state === 'FAILURE' || data.state === 'REVOKED') {
                    clearInterval(intervalId);
                    showToast("Pipeline Failed: " + data.status);
                    resetProcessForm();
                }
            } catch (error) {
                console.error("Polling error:", error);
            }
        }, 2000);
    }

    function resetProcessForm() {
        urlInput.value = '';
        urlInput.disabled = false;
        processBtn.disabled = false;
        setTimeout(() => {
            progressContainer.classList.add('hidden');
            progressBarFill.style.width = '0%';
        }, 3000); // Hide progress after 3 sec on finish
    }

    function renderVideoList() {
        videoListEl.innerHTML = '';
        videos.forEach(v => {
            const li = document.createElement('li');
            li.className = `video-item ${currentVideoId === v.id ? 'active' : ''}`;
            li.innerHTML = `
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; min-width: 0;">
                    ${v.title}
                </span>
                <span class="clip-badge">${v.total_clips} clips</span>
                <button class="btn-delete" title="Delete project" data-folder="${v.folder_name}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
            `;
            li.querySelector('.btn-delete').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteVideo(v.folder_name, v.title);
            });
            li.addEventListener('click', () => selectVideo(v.id));
            videoListEl.appendChild(li);
        });
        lucide.createIcons();
    }

    async function deleteVideo(folderName, title) {
        if (!confirm(`Delete "${title}" and all its clips?`)) return;
        try {
            const res = await fetch(`/api/videos/${encodeURIComponent(folderName)}`, { method: 'DELETE' });
            if (res.ok) {
                showToast(`Deleted "${title}"`);
                currentVideoId = null;
                fetchVideos();
            } else {
                showToast("Failed to delete");
            }
        } catch (err) {
            console.error(err);
            showToast("Delete failed");
        }
    }

    function selectVideo(id) {
        currentVideoId = id;
        renderVideoList(); // Update active state

        const video = videos.find(v => v.id === id);
        if (!video) return;

        headerTitleEl.textContent = video.title;
        headerStatsEl.textContent = `${video.total_clips} Clips Generated`;

        renderClips(video.clips);
    }

    function renderClips(clips) {
        clipsGridEl.innerHTML = '';

        if (clips.length === 0) {
            showEmptyState("This video has no clips generated.");
            return;
        }

        clips.forEach(clip => {
            const card = document.createElement('div');
            card.className = 'clip-card';

            const hookText = clip.metadata?.hook || "No hook provided";
            const score = clip.metadata?.viral_score || "?";

            card.innerHTML = `
                <div class="clip-video-wrapper">
                    <video src="${clip.video_url}" controls preload="metadata" poster=""></video>
                </div>
                <div class="clip-info">
                    <div class="clip-header">
                        <h3>Clip ${clip.clip_idx}</h3>
                        <span class="viral-score">Score: ${score}/10</span>
                    </div>
                    <div class="clip-hook">
                        "${hookText}"
                    </div>
                    <div class="copy-actions">
                        <button class="btn yt" onclick="window.copyCaption('${escapeJsString(clip.platform_captions?.youtube || clip.caption)}')">
                            <i data-lucide="youtube"></i> Copy YouTube
                        </button>
                        <button class="btn tk" onclick="window.copyCaption('${escapeJsString(clip.platform_captions?.tiktok || clip.caption)}')">
                            <i data-lucide="video"></i> Copy TikTok
                        </button>
                        <button class="btn ig" onclick="window.copyCaption('${escapeJsString(clip.platform_captions?.instagram || clip.caption)}')">
                            <i data-lucide="instagram"></i> Copy Instagram
                        </button>
                    </div>
                </div>
            `;
            clipsGridEl.appendChild(card);
        });

        // Re-init icons for dynamic content
        lucide.createIcons();
    }

    function showEmptyState(message) {
        clipsGridEl.innerHTML = `
            <div class="empty-state">
                <i data-lucide="video-off"></i>
                <p>${message}</p>
            </div>
        `;
        lucide.createIcons();
    }

    // Global copy function
    window.copyCaption = async (text) => {
        if (!text || text === 'undefined') {
            showToast("No caption available");
            return;
        }

        try {
            await navigator.clipboard.writeText(text);
            showToast("Caption copied!");
        } catch (err) {
            console.error('Failed to copy text: ', err);
            showToast("Failed to copy");
        }
    };

    function showToast(message) {
        toastEl.textContent = message;
        toastEl.classList.remove('hidden');
        setTimeout(() => {
            toastEl.classList.add('hidden');
        }, 3000);
    }

    function escapeJsString(str) {
        if (!str) return '';
        return str.replace(/'/g, "\\'").replace(/\n/g, "\\n").replace(/\r/g, "");
    }

    // Fetch analytics stats
    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            const stats = await res.json();
            document.getElementById('stat-total-videos').textContent = stats.total_videos;
            document.getElementById('stat-total-clips').textContent = stats.total_clips;
            document.getElementById('stat-today-clips').textContent = stats.today_clips;
            document.getElementById('stat-avg-score').textContent = stats.avg_viral_score > 0 ? stats.avg_viral_score : '–';
        } catch (e) {
            console.error('Failed to fetch stats:', e);
        }
    }

    // Init
    fetchVideos();
    fetchStats();
});

// ─── Tab Switching ────────────────────────────────────────────────────────────
function switchTab(tab) {
    const tabs = ['clipper', 'faceless'];
    tabs.forEach(t => {
        document.getElementById(`tab-${t}`).classList.toggle('active', t === tab);
        document.getElementById(`view-${t}`).classList.toggle('hidden', t !== tab);
        document.getElementById(`panel-${t}`).classList.toggle('hidden', t !== tab);
    });
    lucide.createIcons();
}

// ─── Hook Chip Selection ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.hook-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.hook-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
        });
    });
});

// ─── Faceless Generator ───────────────────────────────────────────────────────
let facelessPollInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateFacelessVideo);
    }
});

async function generateFacelessVideo() {
    const topic = document.getElementById('f-topic').value.trim();
    if (!topic) {
        showFacelessState('error');
        document.getElementById('error-detail-text').textContent = 'Please enter a topic first.';
        return;
    }

    const tone = document.getElementById('f-tone').value;
    const duration = parseInt(document.getElementById('f-duration').value);
    const audience = document.getElementById('f-audience').value.trim() || null;
    const goal = document.getElementById('f-goal').value.trim() || null;
    const template = document.getElementById('f-template').value;
    const font_preset = document.getElementById('f-font').value;
    const color_palette = document.getElementById('f-palette').value;
    const activeChip = document.querySelector('.hook-chip.active');
    const hook_style = activeChip ? (activeChip.dataset.hook || null) : null;

    // Lock UI
    document.getElementById('generate-btn').disabled = true;
    showFacelessState('generating');
    setGenStep('step-script', 'active');

    try {
        const res = await fetch('/api/faceless/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, tone, duration, audience, goal, hook_style, template, font_preset, color_palette })
        });
        const data = await res.json();

        if (!data.task_id) {
            throw new Error(data.detail || 'Could not start generation');
        }

        pollFacelessProgress(data.task_id, topic);
    } catch (err) {
        showFacelessState('error');
        document.getElementById('error-detail-text').textContent = err.message;
        document.getElementById('generate-btn').disabled = false;
    }
}

function pollFacelessProgress(taskId, topic) {
    if (facelessPollInterval) clearInterval(facelessPollInterval);

    facelessPollInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/status/${taskId}`);
            const data = await res.json();

            const pct = data.progress || 0;
            document.getElementById('gen-progress-fill').style.width = `${pct}%`;
            document.getElementById('gen-progress-pct').textContent = `${pct}%`;
            document.getElementById('gen-status-text').textContent = data.status || 'Processing...';

            // Update step indicators based on progress
            if (pct >= 10 && pct < 50) {
                setGenStep('step-script', 'active');
            } else if (pct >= 50 && pct < 70) {
                setGenStep('step-script', 'done');
                setGenStep('step-assets', 'active');
            } else if (pct >= 70 && pct < 80) {
                setGenStep('step-assets', 'done');
                setGenStep('step-voice', 'active');
            } else if (pct >= 80) {
                setGenStep('step-voice', 'done');
                setGenStep('step-render', 'active');
            }

            if (data.state === 'SUCCESS') {
                clearInterval(facelessPollInterval);
                setGenStep('step-render', 'done');
                setTimeout(() => {
                    showFacelessState('done');
                    document.getElementById('done-topic-label').textContent = topic;
                    const outputDir = data.result?.output_dir || '';
                    document.getElementById('done-open-folder').href = `file:///${outputDir.replace(/\\/g, '/')}`;
                    document.getElementById('generate-btn').disabled = false;
                }, 800);
            } else if (data.state === 'FAILURE') {
                clearInterval(facelessPollInterval);
                showFacelessState('error');
                document.getElementById('error-detail-text').textContent = data.status || 'An unknown error occurred.';
                document.getElementById('generate-btn').disabled = false;
            }
        } catch (err) {
            console.error('Poll error:', err);
        }
    }, 3000);
}

function showFacelessState(state) {
    ['idle', 'generating', 'done', 'error'].forEach(s => {
        document.getElementById(`output-${s}`).classList.toggle('hidden', s !== state);
    });
    lucide.createIcons();
}

function setGenStep(stepId, status) {
    const el = document.getElementById(stepId);
    if (!el) return;
    el.classList.remove('active', 'done');
    if (status) el.classList.add(status);
}

window.resetFacelessForm = function () {
    showFacelessState('idle');
    document.getElementById('generate-btn').disabled = false;
    if (facelessPollInterval) clearInterval(facelessPollInterval);
    // Reset step indicators
    ['step-script', 'step-assets', 'step-voice', 'step-render'].forEach(id => setGenStep(id, ''));
    document.getElementById('gen-progress-fill').style.width = '0%';
    document.getElementById('gen-progress-pct').textContent = '0%';
};

