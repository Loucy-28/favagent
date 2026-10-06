const { createApp, ref, reactive, computed, onMounted, watch } = Vue;

createApp({
    setup() {
        const videos = ref([]);
        const allTags = ref([]);
        const platforms = ref([]);
        const stats = reactive({ total: 0, watched: 0, unwatched: 0, pending_reminders: 0, top_categories: [], top_tags: [] });
        const agentStatus = reactive({ ai_enabled: false, model: '', message: '' });
        const preferences = reactive({ reminder_days: 3, auto_classify: true, smart_reminder: true });
        const reminders = ref([]);
        const summary = ref('');
        const smartSuggestion = ref(null);

        const viewMode = ref('time');
        const searchQuery = ref('');
        const filterCategory = ref('');
        const filterPlatform = ref('');

        const showAddVideo = ref(false);
        const showReminders = ref(false);
        const showSettings = ref(false);
        const showAddTag = ref(false);
        const submitting = ref(false);

        const newVideo = reactive({ title: '', url: '', platform: 'other', description: '', author: '', tag_ids: [] });
        const newTag = reactive({ name: '', color: '#6366f1' });

        const toast = reactive({ show: false, message: '', icon: '✅' });
        let debounceTimer = null;

        const allCategories = computed(() => {
            const cats = new Set(videos.value.map(v => v.category));
            return [...cats].sort();
        });

        const filteredVideos = computed(() => {
            let result = videos.value;
            if (filterCategory.value) {
                result = result.filter(v => v.category === filterCategory.value);
            }
            if (filterPlatform.value) {
                result = result.filter(v => v.platform === filterPlatform.value);
            }
            return result;
        });

        const videosByTag = computed(() => {
            const map = {};
            for (const video of videos.value) {
                for (const tag of video.tags) {
                    if (!map[tag.name]) map[tag.name] = [];
                    map[tag.name].push(video);
                }
            }
            return Object.fromEntries(Object.entries(map).sort((a, b) => b[1].length - a[1].length));
        });

        const unreadCount = computed(() => reminders.value.length);

        function showToast(message, icon = '✅') {
            toast.message = message;
            toast.icon = icon;
            toast.show = true;
            setTimeout(() => toast.show = false, 2500);
        }

        async function fetchVideos() {
            const params = new URLSearchParams();
            if (filterPlatform.value) params.set('platform', filterPlatform.value);
            if (searchQuery.value) params.set('search', searchQuery.value);
            const res = await fetch(`/api/videos?${params}`);
            videos.value = await res.json();
        }

        async function fetchTags() {
            const res = await fetch('/api/tags');
            allTags.value = await res.json();
        }

        async function fetchPlatforms() {
            const res = await fetch('/api/platforms');
            platforms.value = await res.json();
        }

        async function fetchStats() {
            const res = await fetch('/api/stats');
            Object.assign(stats, await res.json());
        }

        async function fetchAgentStatus() {
            const res = await fetch('/api/agent/status');
            Object.assign(agentStatus, await res.json());
        }

        async function fetchPreferences() {
            const res = await fetch('/api/preferences');
            Object.assign(preferences, await res.json());
        }

        async function fetchReminders() {
            const res = await fetch('/api/reminders');
            reminders.value = await res.json();
        }

        async function fetchSummary() {
            const res = await fetch('/api/summary');
            const data = await res.json();
            summary.value = data.summary;
        }

        async function fetchSmartSuggestion() {
            const res = await fetch('/api/preferences/smart-suggestion');
            smartSuggestion.value = await res.json();
        }

        async function submitVideo() {
            if (!newVideo.title) return;
            submitting.value = true;
            try {
                const res = await fetch('/api/videos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...newVideo }),
                });
                if (res.ok) {
                    showToast('收藏成功！AI 已完成分类', '🎉');
                    showAddVideo.value = false;
                    Object.assign(newVideo, { title: '', url: '', platform: 'other', description: '', author: '', tag_ids: [] });
                    await Promise.all([fetchVideos(), fetchStats(), fetchTags(), fetchSummary()]);
                } else {
                    const err = await res.json();
                    showToast(err.detail || '添加失败', '❌');
                }
            } catch (e) {
                showToast('网络错误', '❌');
            }
            submitting.value = false;
        }

        async function markWatched(id) {
            await fetch(`/api/videos/${id}/watched`, { method: 'POST' });
            showToast('已标记为观看', '✅');
            await Promise.all([fetchVideos(), fetchStats()]);
        }

        async function reclassify(id) {
            await fetch(`/api/videos/${id}/reclassify`, { method: 'POST' });
            showToast('重新分类完成', '🔄');
            await fetchVideos();
        }

        async function deleteVideo(id) {
            if (!confirm('确定要删除这个视频吗？')) return;
            await fetch(`/api/videos/${id}`, { method: 'DELETE' });
            showToast('已删除', '🗑️');
            await Promise.all([fetchVideos(), fetchStats(), fetchSummary()]);
        }

        async function readReminder(id) {
            await fetch(`/api/reminders/${id}/read`, { method: 'PUT' });
            await fetchReminders();
        }

        async function readAllReminders() {
            await fetch('/api/reminders/read-all', { method: 'PUT' });
            await fetchReminders();
            showToast('全部已读', '✅');
        }

        async function savePreferences() {
            await fetch('/api/preferences', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences),
            });
            showToast('设置已保存', '✅');
        }

        async function createTag() {
            if (!newTag.name) return;
            const res = await fetch('/api/tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newTag),
            });
            if (res.ok) {
                showToast('标签已创建', '🏷️');
                newTag.name = '';
                newTag.color = '#6366f1';
                showAddTag.value = false;
                await fetchTags();
            } else {
                const err = await res.json();
                showToast(err.detail || '创建失败', '❌');
            }
        }

        async function deleteTag(id) {
            await fetch(`/api/tags/${id}`, { method: 'DELETE' });
            await fetchTags();
        }

        function debouncedFetch() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(fetchVideos, 300);
        }

        function formatDate(dateStr) {
            if (!dateStr) return '';
            const d = new Date(dateStr);
            const now = new Date();
            const diff = Math.floor((now - d) / (1000 * 60 * 60 * 24));
            if (diff === 0) return '今天';
            if (diff === 1) return '昨天';
            if (diff < 7) return `${diff}天前`;
            return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
        }

        function getPlatformIcon(platform) {
            const p = platforms.value.find(x => x.value === platform);
            return p ? p.icon : '🔗';
        }

        function getCategoryStyle(category) {
            const styles = {
                '技术编程': 'bg-blue-100 text-blue-700',
                '科技数码': 'bg-cyan-100 text-cyan-700',
                '学习教育': 'bg-green-100 text-green-700',
                '生活日常': 'bg-orange-100 text-orange-700',
                '游戏电竞': 'bg-purple-100 text-purple-700',
                '影视娱乐': 'bg-pink-100 text-pink-700',
                '音乐舞蹈': 'bg-indigo-100 text-indigo-700',
                '运动健身': 'bg-emerald-100 text-emerald-700',
                '财经商业': 'bg-amber-100 text-amber-700',
                '艺术设计': 'bg-rose-100 text-rose-700',
                '资讯新闻': 'bg-slate-100 text-slate-700',
                '其他': 'bg-gray-100 text-gray-700',
            };
            return styles[category] || styles['其他'];
        }

        function getTagColor(tagName) {
            const tag = allTags.value.find(t => t.name === tagName);
            return tag ? tag.color : '#6366f1';
        }

        watch(showSettings, async (val) => {
            if (val) await fetchSmartSuggestion();
        });

        watch(showReminders, async (val) => {
            if (val) await fetchReminders();
        });

        onMounted(async () => {
            await Promise.all([fetchVideos(), fetchTags(), fetchPlatforms(), fetchStats(), fetchAgentStatus(), fetchPreferences(), fetchReminders(), fetchSummary()]);
        });

        return {
            videos, allTags, platforms, stats, agentStatus, preferences, reminders, summary, smartSuggestion,
            viewMode, searchQuery, filterCategory, filterPlatform,
            showAddVideo, showReminders, showSettings, showAddTag, submitting,
            newVideo, newTag, toast,
            allCategories, filteredVideos, videosByTag, unreadCount,
            debouncedFetch, fetchVideos, submitVideo, markWatched, reclassify, deleteVideo,
            readReminder, readAllReminders, savePreferences, createTag, deleteTag,
            formatDate, getPlatformIcon, getCategoryStyle, getTagColor,
        };
    }
}).mount('#app');
