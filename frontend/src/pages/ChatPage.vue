<template>
  <div v-if="chat.sessionLoading" class="flex flex-1 items-center justify-center">
    <Spinner size="lg" label="Loading chat" />
  </div>

  <div v-else-if="chat.isEmpty" class="flex flex-1 items-center justify-center p-24">
    <EmptyState
      icon="chat_bubble"
      title="Nothing here yet"
      description="Ask Director something below to start this chat."
    />
  </div>

  <MessageScroller
    v-else
    ref="scroller"
    class="min-h-0 flex-1"
    content-class="mx-auto flex w-full max-w-760 flex-col gap-32 px-16 py-24 md:px-24"
    :busy="chat.chatLoading"
  >
    <ChatMessageContainer
      v-for="(key, i) in convIds"
      :key="key"
      :conversation="chat.conversations[key]"
      :search-term="chat.chatInput"
      :is-last-conv="i === convIds.length - 1"
    />
  </MessageScroller>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ChatMessageContainer from "@/components/chat/ChatMessageContainer.vue";
import { EmptyState } from "@/components/ui/empty-state";
import { MessageScroller } from "@/components/ui/message-scroller";
import { Spinner } from "@/components/ui/spinner";
import { useChatStore } from "@/stores/chat";

const route = useRoute();
const chat = useChatStore();
const scroller = ref<InstanceType<typeof MessageScroller>>();

const convIds = computed(() => Object.keys(chat.conversations));

watch(
  () => route.params.sessionId as string,
  (id) => id && chat.openSession(id),
  { immediate: true },
);

// A new message from the user brings the thread to the bottom.
watch(
  () => chat.chatLoading,
  async (loading) => {
    if (!loading) return;
    await nextTick();
    scroller.value?.scrollToBottom();
  },
);
</script>
