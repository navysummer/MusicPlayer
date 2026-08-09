<script setup>
import { ref, watch, nextTick } from "vue";

const props = defineProps({
  open: Boolean,
});
const emit = defineEmits(["close", "submit"]);

const url = ref("");
const inputEl = ref(null);

watch(
  () => props.open,
  async (v) => {
    if (v) {
      url.value = "";
      await nextTick();
      inputEl.value && inputEl.value.focus();
    }
  }
);

function submit() {
  const trimmed = url.value.trim();
  if (!trimmed) return;
  emit("submit", trimmed);
  emit("close");
}

function onKey(e) {
  if (e.key === "Enter") submit();
}
</script>

<template>
  <div v-if="open" class="modal" @click.self="$emit('close')">
    <div class="modal-card">
      <h3>网路清音</h3>
      <p class="modal-hint">粘贴一段网络音频地址，mp3 · ogg · aac · flac 等皆可相迎，一缕清音即刻流淌</p>
      <input
        ref="inputEl"
        v-model="url"
        type="text"
        placeholder="https://example.com/song.mp3"
        spellcheck="false"
        @keyup="onKey"
      />
      <div class="modal-actions">
        <button class="ghost" @click="$emit('close')">取消</button>
        <button class="primary" @click="submit">开始播放</button>
      </div>
    </div>
  </div>
</template>