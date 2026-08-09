<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from "vue";
import { invoke } from "@tauri-apps/api/core";
import UrlModal from "./components/UrlModal.vue";
import Toast from "./components/Toast.vue";

const audioEl = ref(null);
const seekEl = ref(null);
const volEl = ref(null);
const timeEl = ref(null);
const lyricsContainer = ref(null);
const currentLyricRef = ref(null);

const emptyVisible = ref(true);
const loadingVisible = ref(false);
const loadingText = ref("正在解析音频…");

const urlModalOpen = ref(false);
const toastVisible = ref(false);
const toastMsg = ref("");
const toastIsErr = ref(false);

const playingState = ref(false);
const iconVolHidden = ref(false);
const iconMuteHidden = ref(true);

const playlist = ref([]);
const currentIndex = ref(-1);
const showPlaylist = ref(true);
const playMode = ref("loop");
const volume = ref(80);
const currentTime = ref(0);
const duration = ref(0);

const state = reactive({
  metadata: null,
  streamUrl: null,
  lyrics: [],
  lrcContent: null,
  idleTimer: null,
  scrubbing: false,
  miniMode: false,
});

const PLAY_MODES = [
  { key: "loop", label: "循环", icon: "loop" },
  { key: "one", label: "单曲", icon: "one" },
  { key: "random", label: "随机", icon: "random" },
  { key: "seq", label: "顺序", icon: "seq" },
];

const coverArt = computed(() => {
  return state.metadata?.cover_art || null;
});

const songTitle = computed(() => {
  return state.metadata?.title || "未加载曲目";
});

const songArtist = computed(() => {
  return state.metadata?.artist || "未知艺术家";
});

const songAlbum = computed(() => {
  return state.metadata?.album || "";
});

const currentIndexDisplay = computed(() => {
  if (currentIndex.value < 0 || playlist.value.length === 0) return "";
  return `${currentIndex.value + 1} / ${playlist.value.length}`;
});

// ---------- LRC parsing ----------
function parseLRC(text) {
  const lines = text.split("\n");
  const result = [];
  const lineRegex = /\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)/;
  const lineRegex2 = /\[(\d{2}):(\d{2}):(\d{2})\.(\d{2,3})\]/;

  for (const line of lines) {
    const match = line.match(lineRegex);
    if (match) {
      const min = parseInt(match[1]);
      const sec = parseInt(match[2]);
      const ms = match[3].length === 2 ? parseInt(match[3]) * 10 : parseInt(match[3]);
      const time = min * 60 + sec + ms / 1000;
      const text = match[4].trim();
      if (text) {
        result.push({ time, text });
      }
    } else {
      const match2 = line.match(lineRegex2);
      if (match2) {
        const min = parseInt(match2[1]);
        const sec = parseInt(match2[2]);
        const ms = match2[4].length === 2 ? parseInt(match2[4]) * 10 : parseInt(match2[4]);
        const time = min * 60 + sec + ms / 1000;
        const text = "";
        result.push({ time, text });
      }
    }
  }
  result.sort((a, b) => a.time - b.time);
  return result;
}

const currentLyricIndex = ref(-1);

function updateLyricIndex(time) {
  const lyrics = state.lyrics;
  if (!lyrics.length) {
    currentLyricIndex.value = -1;
    return;
  }
  let idx = -1;
  for (let i = 0; i < lyrics.length; i++) {
    if (time >= lyrics[i].time) {
      idx = i;
    } else {
      break;
    }
  }
  if (idx !== currentLyricIndex.value) {
    currentLyricIndex.value = idx;
    scrollToCurrentLyric();
  }
}

function scrollToCurrentLyric() {
  nextTick(() => {
    const el = currentLyricRef.value;
    if (el && lyricsContainer.value) {
      const container = lyricsContainer.value;
      const elTop = el.offsetTop;
      const containerHeight = container.clientHeight;
      const targetScroll = elTop - containerHeight / 2 + el.clientHeight / 2;
      container.scrollTo({
        top: targetScroll,
        behavior: "smooth",
      });
    }
  });
}

// ---------- Audio ----------
function loadAudio(meta, streamUrl, lrcContent) {
  state.metadata = meta;
  state.streamUrl = streamUrl;
  state.lyrics = [];

  if (lrcContent) {
    state.lyrics = parseLRC(lrcContent);
  } else if (meta.lyrics) {
    state.lyrics = parseLRC(meta.lyrics);
  }

  currentLyricIndex.value = -1;

  if (audioEl.value.src) {
    audioEl.value.pause();
    audioEl.value.removeAttribute("src");
    audioEl.value.load();
  }
  audioEl.value.src = streamUrl;
  audioEl.value.volume = volume.value / 100;
  audioEl.value.play().catch(() => {});
  loadingVisible.value = false;
  emptyVisible.value = false;
}

async function openMedia(uri) {
  if (!uri) return;
  loadingVisible.value = true;
  loadingText.value = "正在解析音频…";
  emptyVisible.value = false;

  try {
    const res = await invoke("open_media", { uri });
    loadAudio(res.metadata, res.stream_url, res.lrc_content);
  } catch (err) {
    loadingVisible.value = false;
    emptyVisible.value = true;
    toast(typeof err === "string" ? err : String(err), true);
  }
}

async function playTrack(index) {
  if (index < 0 || index >= playlist.value.length) return;
  currentIndex.value = index;
  const track = playlist.value[index];
  if (track.isUrl) {
    emptyVisible.value = false;
    loadingVisible.value = true;
    loadingText.value = "正在连接网络…";
    state.metadata = track.metadata;
    state.streamUrl = track.path;
    state.lyrics = [];

    if (audioEl.value.src) {
      audioEl.value.pause();
      audioEl.value.removeAttribute("src");
      audioEl.value.load();
    }
    audioEl.value.src = track.path;
    audioEl.value.volume = volume.value / 100;
    audioEl.value.play().catch(() => {});
    loadingVisible.value = false;
  } else {
    await openMedia(track.path);
  }
}

function playNext() {
  const mode = playMode.value;
  const len = playlist.value.length;
  if (len === 0) return;

  let next;
  if (mode === "one") {
    next = currentIndex.value;
  } else if (mode === "random") {
    next = Math.floor(Math.random() * len);
  } else if (mode === "seq") {
    next = currentIndex.value + 1;
    if (next >= len) {
      playingState.value = false;
      return;
    }
  } else {
    next = (currentIndex.value + 1) % len;
  }
  playTrack(next);
}

function playPrev() {
  const len = playlist.value.length;
  if (len === 0) return;
  let prev;
  if (playMode.value === "random") {
    prev = Math.floor(Math.random() * len);
  } else {
    prev = currentIndex.value - 1;
    if (prev < 0) prev = len - 1;
  }
  playTrack(prev);
}

// ---------- File dialog ----------
async function openFileDialog() {
  try {
    const paths = await invoke("open_file_dialog");
    if (paths && paths.length > 0) {
      for (const p of paths) {
        try {
          const meta = await invoke("get_metadata", { path: p });
          playlist.value.push({ path: p, metadata: meta, isUrl: false });
        } catch {
          playlist.value.push({
            path: p,
            metadata: { title: "未知曲目", artist: "", album: "", cover_art: null, duration: 0 },
            isUrl: false,
          });
        }
      }
      if (currentIndex.value < 0) {
        await playTrack(0);
      }
    }
  } catch (err) {
    toast(String(err), true);
  }
}

async function openFolderDialog() {
  try {
    const dir = await invoke("open_folder_dialog");
    if (dir) {
      loadingVisible.value = true;
      loadingText.value = "正在扫描文件夹…";
      const paths = await invoke("scan_folder", { path: dir });
      for (const p of paths) {
        try {
          const meta = await invoke("get_metadata", { path: p });
          playlist.value.push({ path: p, metadata: meta, isUrl: false });
        } catch {
          playlist.value.push({
            path: p,
            metadata: { title: "未知曲目", artist: "", album: "", cover_art: null, duration: 0 },
            isUrl: false,
          });
        }
      }
      loadingVisible.value = false;
      if (currentIndex.value < 0 && playlist.value.length > 0) {
        await playTrack(0);
      }
    }
  } catch (err) {
    loadingVisible.value = false;
    toast(String(err), true);
  }
}

function onUrlSubmit(url) {
  playlist.value.push({
    path: url,
    metadata: { title: url.split("/").pop() || "网络曲目", artist: "网络来源", album: "", cover_art: null, duration: 0 },
    isUrl: true,
  });
  if (currentIndex.value < 0) {
    playTrack(playlist.value.length - 1);
  }
}

async function removeTrack(index) {
  const wasCurrent = index === currentIndex.value;
  playlist.value.splice(index, 1);
  if (wasCurrent) {
    if (playlist.value.length > 0) {
      await playTrack(Math.min(index, playlist.value.length - 1));
    } else {
      currentIndex.value = -1;
      state.metadata = null;
      state.streamUrl = null;
      state.lyrics = [];
      emptyVisible.value = true;
      if (audioEl.value) {
        audioEl.value.pause();
        audioEl.value.removeAttribute("src");
      }
    }
  } else if (index < currentIndex.value) {
    currentIndex.value--;
  }
}

function clearPlaylist() {
  playlist.value = [];
  currentIndex.value = -1;
  state.metadata = null;
  state.streamUrl = null;
  state.lyrics = [];
  emptyVisible.value = true;
  if (audioEl.value) {
    audioEl.value.pause();
    audioEl.value.removeAttribute("src");
  }
}

function cyclePlayMode() {
  const keys = PLAY_MODES.map((m) => m.key);
  const idx = keys.indexOf(playMode.value);
  playMode.value = keys[(idx + 1) % keys.length];
}

// ---------- Audio events ----------
function onLoadedMetadata() {
  loadingVisible.value = false;
  emptyVisible.value = false;
  duration.value = audioEl.value.duration || 0;
  updateSeek();
}

function onPlaying() {
  playingState.value = true;
}

function onPause() {
  playingState.value = false;
}

function onEnded() {
  playingState.value = false;
  playNext();
}

function onError() {
  loadingVisible.value = false;
  toast("音频加载失败，请检查文件或网络地址", true);
}

function onTimeUpdate() {
  if (state.scrubbing) return;
  const v = audioEl.value;
  if (!v) return;
  currentTime.value = v.currentTime;
  updateSeek();
  updateLyricIndex(v.currentTime);
}

function updateSeek() {
  const v = audioEl.value;
  if (!v) return;
  const live = !v.duration || !isFinite(v.duration) || v.duration === Infinity;
  if (live) {
    if (seekEl.value) {
      seekEl.value.value = 0;
      seekEl.value.style.background = `linear-gradient(90deg, rgba(219,181,121,.8) 0%, rgba(219,181,121,.8) 0%, rgba(255,235,200,.08) 0% 100%)`;
    }
    if (timeEl.value) {
      timeEl.value.innerHTML = `${fmtTime(v.currentTime)}<i>/</i> 直播`;
    }
    return;
  }
  const ratio = v.currentTime / v.duration;
  if (seekEl.value) {
    seekEl.value.value = Math.round(ratio * 1000);
    const fill = ratio * 100;
    seekEl.value.style.background = `linear-gradient(90deg, #d8b97f 0%, #c9a25f ${fill}%, rgba(255,235,200,.08) ${fill}% 100%)`;
  }
  if (timeEl.value) {
    timeEl.value.innerHTML = `${fmtTime(v.currentTime)}<i>/</i>${fmtTime(v.duration)}`;
  }
}

// ---------- Controls ----------
function onSeekInput() {
  const v = audioEl.value;
  if (!v.duration || !isFinite(v.duration)) return;
  const t = (seekEl.value.value / 1000) * v.duration;
  v.currentTime = t;
  currentTime.value = t;
  updateLyricIndex(t);
}

function onSeekDown() {
  state.scrubbing = true;
}

function onSeekUp() {
  state.scrubbing = false;
}

function togglePlay() {
  const v = audioEl.value;
  if (!v.src) return;
  if (v.paused || v.ended) v.play().catch(() => {});
  else v.pause();
}

function seekBy(delta) {
  const v = audioEl.value;
  if (!v.duration || !isFinite(v.duration)) return;
  v.currentTime = Math.max(0, Math.min(v.duration, v.currentTime + delta));
}

function onVolInput() {
  const v = Number(volEl.value.value);
  volume.value = v;
  audioEl.value.volume = v / 100;
  audioEl.value.muted = v === 0;
  updateMuteIcon();
}

function toggleMute() {
  audioEl.value.muted = !audioEl.value.muted;
  updateMuteIcon();
}

function updateMuteIcon() {
  const muted = audioEl.value.muted || audioEl.value.volume === 0;
  iconVolHidden.value = muted;
  iconMuteHidden.value = !muted;
}

// ---------- Drag & drop ----------
const dropHintVisible = ref(false);

// ---------- Utilities ----------
function fmtTime(sec) {
  if (!isFinite(sec) || sec == null) return "00:00";
  sec = Math.max(0, Math.floor(sec));
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function fmtDuration(sec) {
  if (!sec || !isFinite(sec)) return "--:--";
  return fmtTime(sec);
}

let toastT = null;
function toast(msg, isErr = false) {
  toastMsg.value = msg;
  toastIsErr.value = isErr;
  toastVisible.value = true;
  clearTimeout(toastT);
  toastT = setTimeout(() => {
    toastVisible.value = false;
  }, 3600);
}

// ---------- Keyboard ----------
function onKeydown(e) {
  if (urlModalOpen.value) {
    if (e.key === "Escape") urlModalOpen.value = false;
    return;
  }
  switch (e.key) {
    case " ":
      e.preventDefault();
      togglePlay();
      break;
    case "ArrowRight":
      seekBy(5);
      break;
    case "ArrowLeft":
      seekBy(-5);
      break;
    case "ArrowUp":
      e.preventDefault();
      if (volume.value < 100) {
        volume.value = Math.min(100, volume.value + 5);
        audioEl.value.volume = volume.value / 100;
        volEl.value.value = volume.value;
      }
      break;
    case "ArrowDown":
      e.preventDefault();
      if (volume.value > 0) {
        volume.value = Math.max(0, volume.value - 5);
        audioEl.value.volume = volume.value / 100;
        volEl.value.value = volume.value;
      }
      break;
    case "m":
    case "M":
      toggleMute();
      break;
    case "n":
    case "N":
      playNext();
      break;
    case "p":
    case "P":
      playPrev();
      break;
  }
}

// ---------- Lifecycle ----------
onMounted(() => {
  document.addEventListener("keydown", onKeydown);
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => e.preventDefault());

  const win = window.__TAURI__?.getCurrentWindow();
  if (win) {
    win.onDragDropEvent(async (event) => {
      if (!event.payload) return;
      if (event.payload.type === "over" || event.payload.type === "enter")
        dropHintVisible.value = true;
      if (event.payload.type === "leave") dropHintVisible.value = false;
      if (event.payload.type === "drop") {
        dropHintVisible.value = false;
        const paths = event.payload.paths;
        if (paths && paths.length) {
          for (const p of paths) {
            try {
              const meta = await invoke("get_metadata", { path: p });
              playlist.value.push({ path: p, metadata: meta, isUrl: false });
            } catch {
              playlist.value.push({
                path: p,
                metadata: { title: "未知曲目", artist: "", album: "", cover_art: null, duration: 0 },
                isUrl: false,
              });
            }
          }
          if (currentIndex.value < 0) {
            await playTrack(0);
          }
        }
      }
    });
  }

  window.addEventListener("beforeunload", () => {
    invoke("stop_playback").catch(() => {});
  });
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKeydown);
  invoke("stop_playback").catch(() => {});
});
</script>

<template>
  <div class="app">
    <!-- ===== Top bar ===== -->
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark"><span class="brand-mark-inner zheng"></span></div>
        <div class="brand-text">
          <span class="brand-name">琴韵</span>
          <span class="brand-sub">QIN YUN</span>
        </div>
      </div>
      <div class="top-actions">
        <button class="tbtn ghost" @click="urlModalOpen = true">
          <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M10.6 13.4a1 1 0 0 1-1.4 0 4 4 0 0 1 0-5.7l4-4a4 4 0 1 1 5.7 5.7l-1.8 1.8a1 1 0 1 1-1.4-1.4l1.8-1.8a2 2 0 0 0-2.9-2.9l-4 4a2 2 0 0 0 0 2.9 1 1 0 0 1 0 1.4Z"/><path fill="currentColor" d="M13.4 10.6a1 1 0 0 1 1.4 0 4 4 0 0 1 0 5.7l-4 4a4 4 0 1 1-5.7-5.7l1.8-1.8a1 1 0 1 1 1.4 1.4l-1.8 1.8a2 2 0 0 0 2.9 2.9l4-4a2 2 0 0 0 0-2.9 1 1 0 0 1 0-1.4Z"/></svg>
          网络播放
        </button>
        <button class="tbtn primary" @click="openFileDialog">
          <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 3a1 1 0 0 1 1 1v6h6a1 1 0 1 1 0 2h-6v6a1 1 0 1 1-2 0v-6H5a1 1 0 1 1 0-2h6V4a1 1 0 0 1 1-1Z"/></svg>
          打开文件
        </button>
        <button class="tbtn ghost" @click="openFolderDialog">
          <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M10 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-8l-2-2Z"/></svg>
          打开文件夹
        </button>
      </div>
    </header>

    <!-- ===== Main area ===== -->
    <main class="main-area">
      <!-- Empty state -->
      <div v-if="emptyVisible" class="empty">
        <div class="empty-icon"><span class="empty-icon-inner"></span></div>
        <h2>银屏静候 · 一曲清音</h2>
        <p>打开本地音律，或粘贴一曲网络清音，<br/>mp3 · flac · wav · ogg · aac · m4a · wma 皆可相迎</p>
        <div class="empty-buttons">
          <button class="primary big" @click="openFileDialog">选择文件</button>
          <button class="ghost big" @click="openFolderDialog">选择文件夹</button>
          <button class="ghost big" @click="urlModalOpen = true">粘贴网络地址</button>
        </div>
      </div>

      <!-- Loading -->
      <div v-show="loadingVisible" class="loading">
        <div class="spinner"></div>
        <p>{{ loadingText }}</p>
      </div>

      <!-- Drop hint -->
      <div v-show="dropHintVisible" class="drop-hint">
        <svg viewBox="0 0 24 24" width="28" height="28"><path fill="currentColor" d="M12 3a1 1 0 0 1 1 1v6h6a1 1 0 1 1 0 2h-6v6a1 1 0 1 1-2 0v-6H5a1 1 0 1 1 0-2h6V4a1 1 0 0 1 1-1Z"/></svg>
        松卷以开
      </div>

      <!-- Now playing -->
      <div v-if="!emptyVisible && !loadingVisible" class="now-playing">
        <div class="cover-section">
          <div class="cover-frame" :class="{ active: playingState }">
            <div v-if="coverArt" class="cover-art" :style="{ backgroundImage: `url(${coverArt})` }"></div>
            <div v-else class="cover-placeholder">
              <svg viewBox="0 0 24 24" width="48" height="48"><path fill="currentColor" opacity=".4" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16Z"/><path fill="currentColor" opacity=".4" d="M12 7a1 1 0 0 0-1 1v4.76A3 3 0 1 0 13 16V9h3a1 1 0 1 0 0-2h-4Z"/></svg>
            </div>
            <div class="cover-ring"></div>
          </div>
          <div class="song-info">
            <h3 class="song-title">{{ songTitle }}</h3>
            <p class="song-artist">{{ songArtist }}</p>
            <p v-if="songAlbum" class="song-album">{{ songAlbum }}</p>
          </div>
        </div>
        <div class="lyrics-section" v-if="state.lyrics.length > 0">
          <div ref="lyricsContainer" class="lyrics-container">
            <div
              v-for="(line, i) in state.lyrics"
              :key="i"
              :ref="i === currentLyricIndex ? currentLyricRef : undefined"
              class="lyric-line"
              :class="{ active: i === currentLyricIndex, passed: i < currentLyricIndex }"
            >
              {{ line.text }}
            </div>
          </div>
        </div>
        <div class="lyrics-section no-lyrics" v-else>
          <div class="lyrics-placeholder">
            <p>清音流淌 · 无词亦成韵</p>
          </div>
        </div>
      </div>
    </main>

    <!-- ===== Playlist sidebar ===== -->
    <aside class="playlist-sidebar" :class="{ open: showPlaylist }">
      <div class="playlist-header">
        <span class="playlist-title">曲 卷</span>
        <span class="playlist-count">{{ currentIndexDisplay }}</span>
        <div class="playlist-actions">
          <button class="icon-btn" @click="showPlaylist = !showPlaylist" title="切换列表">
            <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M3 6h18v2H3V6Zm0 5h18v2H3v-2Zm0 5h18v2H3v-2Z"/></svg>
          </button>
          <button class="icon-btn" @click="clearPlaylist" title="清空列表">
            <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M18 6v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6H4V4h5V3h6v1h5v2h-2Zm-3 0H9v11h6V6Z"/></svg>
          </button>
        </div>
      </div>
      <div class="playlist-items">
        <div
          v-for="(item, i) in playlist"
          :key="i"
          class="playlist-item"
          :class="{ active: i === currentIndex }"
          @dblclick="playTrack(i)"
        >
          <div class="item-info">
            <span class="item-title">{{ item.metadata?.title || '未知曲目' }}</span>
            <span class="item-artist">{{ item.metadata?.artist || '' }}</span>
          </div>
          <div class="item-controls">
            <span class="item-duration">{{ fmtDuration(item.metadata?.duration) }}</span>
            <button class="item-remove" @click.stop="removeTrack(i)" title="移除">
              <svg viewBox="0 0 24 24" width="12" height="12"><path fill="currentColor" d="M18 6v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6H4V4h5V3h6v1h5v2h-2Zm-3 0H9v11h6V6Z"/></svg>
            </button>
          </div>
        </div>
        <div v-if="playlist.length === 0" class="playlist-empty">
          <p>曲卷空空 · 静待佳音</p>
        </div>
      </div>
    </aside>

    <!-- ===== Player bar ===== -->
    <footer class="player-bar">
      <div class="seek-row">
        <input ref="seekEl" id="seek" class="seek" type="range" min="0" max="1000" value="0" step="1"
          @input="onSeekInput"
          @pointerdown="onSeekDown"
          @pointerup="onSeekUp" />
      </div>
      <div class="controls-row">
        <button class="cbtn" title="上一首" @click="playPrev">
          <svg viewBox="0 0 24 24"><path fill="currentColor" d="M6 6h2v12H6V6Zm3.5 6 8.5 6V6l-8.5 6Z"/></svg>
        </button>
        <button class="cbtn play" title="播放 / 暂停" @click="togglePlay">
          <svg v-show="!playingState" viewBox="0 0 24 24"><path fill="currentColor" d="M7 4.5a1 1 0 0 1 1.6-.8l12 8.5a1 1 0 0 1 0 1.6l-12 8.5a1 1 0 0 1-1.6-.8v-17Z"/></svg>
          <svg v-show="playingState" viewBox="0 0 24 24"><path fill="currentColor" d="M6 4.5a1 1 0 0 1 2 0v15a1 1 0 1 1-2 0v-15Zm10 0a1 1 0 1 1 2 0v15a1 1 0 1 1-2 0v-15Z"/></svg>
        </button>
        <button class="cbtn" title="下一首" @click="playNext">
          <svg viewBox="0 0 24 24"><path fill="currentColor" d="M18 6v12h-2V6h2Zm-8.5 6L6 6v12l3.5-3V6l8.5 6-8.5 6v-6Z"/></svg>
        </button>
        <span ref="timeEl" class="time" id="time">00:00 <i>/</i> 00:00</span>
        <div class="spacer"></div>
        <button class="cbtn mode-btn" :title="'播放模式: ' + PLAY_MODES.find(m => m.key === playMode)?.label" @click="cyclePlayMode">
          <svg v-if="playMode === 'loop'" viewBox="0 0 24 24"><path fill="currentColor" d="M17 2l4 4-4 4V7H7v4H5V5h12V2ZM7 22l-4-4 4-4v3h12v-4h2v6H7v3Z"/></svg>
          <svg v-else-if="playMode === 'one'" viewBox="0 0 24 24"><path fill="currentColor" d="M17 2l4 4-4 4V7H7v4H5V5h12V2ZM7 22l-4-4 4-4v3h12v-4h2v6H7v3Z"/><text x="12" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">1</text></svg>
          <svg v-else-if="playMode === 'random'" viewBox="0 0 24 24"><path fill="currentColor" d="M17 17h-2l-4-5-4 5H5v-2h2l4-5-4-5H5V3h2l4 5 4-5h2v2h-2l-4 5 4 5h2v2Z"/></svg>
          <svg v-else viewBox="0 0 24 24"><path fill="currentColor" d="M7 2v2h10V2h2v3H5V2h2Zm0 5h10v2H7V7Zm-2 5h14v2H5v-2Zm2 5h10v2H7v-2Zm-2 5h14v2H5v-2Z"/></svg>
        </button>
        <div class="volume">
          <button class="cbtn" title="静音" @click="toggleMute">
            <svg v-show="!iconMuteHidden" viewBox="0 0 24 24"><path fill="currentColor" d="M4 9v6h4l5 4V5L8 9H4Zm12 3a3 3 0 0 0-1.5-2.6v5.2A3 3 0 0 0 16 12Zm-1.5-6.9v2.1a5.5 5.5 0 0 1 0 9.6v2.1a7.5 7.5 0 0 0 0-13.8Z"/></svg>
            <svg v-show="iconMuteHidden" viewBox="0 0 24 24"><path fill="currentColor" d="M4 9v6h4l5 4V5L8 9H4Zm12.3-2.3 1.2 1.2-3.3 3.3 3.3 3.3-1.2 1.2-3.3-3.3-3.3 3.3-1.2-1.2 3.3-3.3-3.3-3.3 1.2-1.2 3.3 3.3 3.3-3.3Z"/></svg>
          </button>
          <input ref="volEl" id="vol" class="vol" type="range" min="0" max="100" :value="volume"
            @input="onVolInput" />
        </div>
      </div>
    </footer>

    <!-- audio element (hidden) -->
    <audio
      ref="audioEl"
      preload="auto"
      @loadedmetadata="onLoadedMetadata"
      @playing="onPlaying"
      @pause="onPause"
      @ended="onEnded"
      @timeupdate="onTimeUpdate"
      @error="onError"
    ></audio>

    <!-- modals & toast -->
    <UrlModal :open="urlModalOpen" @close="urlModalOpen = false" @submit="onUrlSubmit" />
    <Toast :message="toastMsg" :is-err="toastIsErr" :visible="toastVisible" />
  </div>
</template>