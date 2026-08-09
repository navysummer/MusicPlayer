<script setup>
defineProps({
  message: String,
  isErr: Boolean,
  visible: Boolean,
});
</script>

<template>
  <transition name="toast">
    <div v-if="visible" class="toast" :class="{ err: isErr }">
      {{ message }}
    </div>
  </transition>
</template>