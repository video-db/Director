<template>
  <div
    v-if="chat.sessionLoading"
    class="vdb-c-flex vdb-c-w-full vdb-c-flex-1 vdb-c-items-center vdb-c-justify-center"
  >
    <EllipsesLoading />
  </div>

  <div
    v-else-if="chat.isEmpty"
    class="vdb-c-flex vdb-c-w-full vdb-c-flex-1 vdb-c-flex-col vdb-c-items-center vdb-c-justify-center vdb-c-gap-8 vdb-c-text-center"
  >
    <p class="vdb-c-text-lg vdb-c-font-semibold vdb-c-text-kilvish-900">
      Nothing here yet
    </p>
    <p class="vdb-c-text-sm vdb-c-text-vdb-darkishgrey">
      Ask Director something below to start this chat.
    </p>
  </div>

  <template v-else>
    <ChatMessageContainer
      v-for="(key, i) in convIds"
      :key="key"
      :conversation="chat.conversations[key]"
      :search-term="chat.chatInput"
      :is-last-conv="i === convIds.length - 1"
      class="vdb-c-px-30 vdb-c-transition-all vdb-c-duration-300 vdb-c-ease-in-out md:vdb-c-px-60"
      :class="{ 'last-conv-height': i === convIds.length - 1 }"
    />
  </template>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute } from "vue-router";

import ChatMessageContainer from "@/components/chat/ChatMessageContainer.vue";
import EllipsesLoading from "@/components/chat/elements/EllipsesLoading.vue";
import { useChatStore } from "@/stores/chat";

const route = useRoute();
const chat = useChatStore();

const convIds = computed(() => Object.keys(chat.conversations));

watch(
  () => route.params.sessionId as string,
  (id) => id && chat.openSession(id),
  { immediate: true },
);
</script>
