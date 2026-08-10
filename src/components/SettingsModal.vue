<script setup>
import { ref, onMounted } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { getVersion } from "@tauri-apps/api/app";

defineProps({
  open: { type: Boolean, default: false },
});
const emit = defineEmits(["close"]);

const links = [
  { icon: "G", label: "GitHub", href: "https://github.com/navysummer", sub: "github.com/navysummer" },
  { icon: "博", label: "博客", href: "https://www.cnblogs.com/navysummer", sub: "cnblogs.com/navysummer" },
];

const currentVersion = ref("0.0.1");
const checking = ref(false);
const checkResult = ref(null);

onMounted(async () => {
  try {
    const v = await getVersion();
    currentVersion.value = v.replace(/^v/, "");
  } catch {
    currentVersion.value = "0.0.1";
  }
});

async function openExternal(url) {
  try {
    await invoke("open_external", { url });
  } catch {
    window.open(url, "_blank");
  }
}

async function checkForUpdate() {
  checking.value = true;
  checkResult.value = null;
  try {
    const res = await invoke("check_update");
    checkResult.value = {
      type: res.has_update ? "update" : res.has_release ? "ok" : "none",
      latestVersion: res.latest_version,
      url: res.url,
      message: "",
    };
  } catch (err) {
    checkResult.value = {
      type: "err",
      latestVersion: "",
      url: "",
      message: typeof err === "string" ? err : String(err),
    };
  } finally {
    checking.value = false;
  }
}

function goDownload() {
  if (checkResult.value && checkResult.value.url) {
    openExternal(checkResult.value.url);
  }
}
</script>

<template>
  <div v-if="open" class="modal" @click.self="emit('close')">
    <div class="modal-card settings-card">
      <h3>设置</h3>
      <div class="settings-tabs">
        <button class="tab active">关于</button>
      </div>

      <div class="settings-panel">
        <div class="about-head">
          <div class="about-mark"><span class="about-mark-inner"></span></div>
          <div class="about-title">
            <span class="about-name">琴韵</span>
            <span class="about-sub">QIN·YUN　古风音乐播放器</span>
          </div>
        </div>

        <div class="about-section">
          <h4>书卷雅意 · 一曲清音</h4>
          <ul class="feature-list">
            <li>百里音律收一匣：古典唯美风格、金玉雕纹，声色俱佳。</li>
            <li>一卷在手，万格式可听：本地音频、网络清音随取随放，今朝即开即赏。</li>
            <li>跨平台同游：一款可伴 Windows、macOS、Linux 世代传抄。</li>
            <li>静谧省心：即点即放，无需额外安装任何环境。</li>
            <li>体贴细节：倍速、音量、进度、歌词、列表、拖曳任意快件。</li>
          </ul>
        </div>

        <div class="about-divider"></div>

        <div class="about-section">
          <h4>版本</h4>
          <div class="update-row">
            <span class="version-tag">当前版本 v{{ currentVersion }}</span>
            <button class="update-btn" @click="checkForUpdate" :disabled="checking">
              <span v-if="checking" class="mini-spinner"></span>
              {{ checking ? "检查中…" : "检查更新" }}
            </button>
          </div>
          <div v-if="checkResult" class="update-result" :class="checkResult.type">
            <template v-if="checkResult.type === 'update'">
              <p>发现新版本 v{{ checkResult.latestVersion }}，是否前往下载？</p>
              <div class="update-actions">
                <button class="primary" @click="goDownload">前往下载</button>
                <button class="ghost" @click="checkResult = null">知道了</button>
              </div>
            </template>
            <p v-else-if="checkResult.type === 'ok'">当前已是最新版本，无需更新。</p>
            <p v-else-if="checkResult.type === 'none'">仓库暂无发布版本，敬请期待。</p>
            <p v-else>{{ checkResult.message }}</p>
          </div>
        </div>

        <div class="about-divider"></div>

        <div class="about-section">
          <h4>作者</h4>
          <ul class="author-list">
            <li>
              <span class="author-icon">名</span>
              <span class="author-main">
                <span class="author-name">navysummer</span>
                <span class="author-role">独立创作者</span>
              </span>
            </li>
            <li v-for="l in links" :key="l.href">
              <span class="author-icon">{{ l.icon }}</span>
              <span class="author-main">
                <button class="link" @click="openExternal(l.href)">{{ l.label }}</button>
                <span class="author-role">{{ l.sub }}</span>
              </span>
            </li>
            <li>
              <span class="author-icon">微</span>
              <span class="author-main">
                <span class="author-name">navysummer1001</span>
                <span class="author-role">微信 ID</span>
              </span>
            </li>
          </ul>
          <p class="about-foot">愿此卷录君心 · 谢谢使用琴韵</p>
        </div>
      </div>

      <div class="modal-actions">
        <button class="ghost" @click="emit('close')">关闭</button>
      </div>
    </div>
  </div>
</template>