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
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px;">
                    ${v.title}
                </span>
                <span class="clip-badge">${v.total_clips} clips</span>
            `;
            li.addEventListener('click', () => selectVideo(v.id));
            videoListEl.appendChild(li);
        });
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

    // Init
    fetchVideos();
});
