<!-- eslint-disable vue/no-v-html -->
<template>
  <div class="flex w-full flex-col gap-8 text-left">
    <LoadingMessage
      v-if="!isUser && !isInterimText"
      :status="isMainResponse && message?.status === 'error' ? 'error' : (content.status ?? 'progress')"
      :message="content.status_message"
      :is-focused="isMainResponse"
    />

    <div
      v-if="content.status === 'success' || content.status === 'error' || isUser"
      class="markdown-body"
      :class="{ 'text-text-neutral-secondary': isInterimText }"
      v-html="html"
    />
    <div v-else-if="content.status === 'progress'" class="flex flex-col gap-8 py-4">
      <Skeleton class="h-14 w-3/4" />
      <Skeleton class="h-14 w-1/2" />
      <Skeleton class="h-14 w-2/3" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { Skeleton } from "@/components/ui/skeleton";
import { renderMarkdown } from "@/lib/markdown";
import { useChatStore } from "@/stores/chat";
import type { ContentBase } from "@/types";

import LoadingMessage from "./elements/LoadingMessage.vue";

const props = defineProps<{
  content: ContentBase & { text?: string };
  isUser?: boolean;
  convId?: string;
  msgId?: string;
}>();

const chat = useChatStore();
const html = computed(() => renderMarkdown(props.content.text || ""));
const message = computed(() =>
  props.convId && props.msgId ? chat.conversations[props.convId]?.[props.msgId] : undefined,
);

// The model's text before a tool call is narration; only its last text, once
// the turn is done, is the reply.
const isMainResponse = computed(() => {
  if (props.content.agent_name !== "assistant") return false;
  if (["progress", "awaiting_approval"].includes(message.value?.status as string)) return false;
  const texts = (message.value?.content ?? []).filter((c) => c.agent_name === "assistant");
  return texts.length === 0 || texts[texts.length - 1] === props.content;
});
const isInterimText = computed(
  () => props.content.agent_name === "assistant" && !isMainResponse.value,
);
</script>
