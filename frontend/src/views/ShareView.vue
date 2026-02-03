<script setup>
import { useRoute } from "vue-router";
import { ChatInterface } from "@videodb/chat-vue";
import "@videodb/chat-vue/dist/style.css";

const route = useRoute();
const sessionId = route.params.sessionId;
const BACKEND_URL = import.meta.env.VITE_APP_BACKEND_URL;
import { publicUseVideoDBAgent } from "../hooks/shareViewHandler";
const publicHook = (config) => publicUseVideoDBAgent(config, sessionId);
</script>

<template>
  <div class="public-share-page">
    <chat-interface
      :custom-chat-hook="publicHook"
      :chat-hook-config="{
        socketUrl: `${BACKEND_URL}/chat`,
        httpUrl: `${BACKEND_URL}`,
        debug: true,
        sessionId: sessionId,
      }"
      :show-sidebar="false"
      :show-header="false"
      :show-chat-input="false"
      :sidebar-config="{ enabled: false }"
      :default-screen-config="{ enableVideoView: false }"
      size="full"
    />
  </div>
</template>

<style scoped>
.public-share-page {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>
