<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
import { ChatInterface } from "@videodb/chat-vue";
import "@videodb/chat-vue/dist/style.css";

const BACKEND_URL = import.meta.env.VITE_APP_BACKEND_URL;
const chatInterfaceRef = ref(null);
const isGenerating = ref(false);
const currentSessionId = ref(null);
const stopPending = ref(false);

const stopGeneration = async () => {
  if (currentSessionId.value) {
    stopPending.value = true;
    isGenerating.value = false;
    try {
      await fetch(`${BACKEND_URL}/session/${currentSessionId.value}/stop`, {
        method: "POST",
      });
    } finally {
      stopPending.value = false;
    }
  }
};

// Watch the chat component's conversations reactive object for in-progress assistant messages.
// conversations shape: { [conv_id]: { [msg_id]: { session_id, status, sender, ... } } }
watch(
  () => chatInterfaceRef.value?.conversations,
  (convs) => {
    if (!convs || stopPending.value) return;
    for (const convMessages of Object.values(convs)) {
      if (!convMessages) continue;
      for (const msg of Object.values(convMessages)) {
        if (!msg) continue;
        if (msg.sender === "assistant" && msg.status === "progress") {
          isGenerating.value = true;
          currentSessionId.value = msg.session_id;
          return;
        }
      }
    }
    isGenerating.value = false;
  },
  { deep: true }
);

const handleKeyDown = (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "k") {
    event.preventDefault();
    chatInterfaceRef.value.createNewSession();
    chatInterfaceRef.value.chatInputRef.focus();
  }
};

onMounted(() => {
  window.addEventListener("keydown", handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeyDown);
});
</script>

<template>
  <main>
    <chat-interface
      ref="chatInterfaceRef"
      :chat-hook-config="{
        socketUrl: `${BACKEND_URL}/chat`,
        httpUrl: `${BACKEND_URL}`,
        debug: true,
      }"
    />
    <button
      v-if="isGenerating"
      type="button"
      class="stop-btn"
      aria-label="Stop generation"
      @click="stopGeneration"
      title="Stop generation"
    >
      &#9632; Stop
    </button>
  </main>
</template>

<style>
:root {
  --popper-theme-background-color: #333333;
  --popper-theme-background-color-hover: #333333;
  --popper-theme-text-color: #ffffff;
  --popper-theme-border-width: 0px;
  --popper-theme-border-style: solid;
  --popper-theme-border-radius: 8px;
  --popper-theme-padding: 4px 8px;
  --popper-theme-box-shadow: 0px 6px 6px rgba(0, 0, 0, 0.08);
}

.template {
  height: 100vh;
  width: 100vw;
}

main {
  overflow: scroll;
  height: 100%;
}
html {
  overflow: hidden;
}

/* For WebKit-based browsers (Chrome, Safari) */
::-webkit-scrollbar {
  width: 12px; /* Width of the scrollbar */
}

::-webkit-scrollbar-track {
  background: #f1f1f1; /* Background of the scrollbar track */
}

::-webkit-scrollbar-thumb {
  background-color: #888; /* Scrollbar thumb color */
  border-radius: 6px; /* Rounded corners */
  border: 3px solid #f1f1f1; /* Space around the thumb */
}

::-webkit-scrollbar-thumb:hover {
  background-color: #555; /* Thumb color on hover */
}

/* For Mozilla Firefox */
* {
  scrollbar-width: thin; /* Makes the scrollbar narrower */
  scrollbar-color: #888 #f1f1f1; /* Thumb and track colors */
}

.stop-btn {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: #1a1a1a;
  color: #fff;
  border: 1px solid #444;
  border-radius: 20px;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: background 0.15s;
}

.stop-btn:hover {
  background: #333;
}
</style>
