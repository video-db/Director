<template>
  <div class="flex w-full flex-col gap-24">
    <ChatMessage
      v-for="message in messages"
      :key="message.msg_id"
      :message="message"
      :is-last-conv="isLastConv"
      :search-term="searchTerm"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { Message } from "@/types";

import ChatMessage from "./ChatMessage.vue";

const props = defineProps<{
  conversation: Record<string, Message>;
  isLastConv?: boolean;
  searchTerm?: string;
}>();

const messages = computed(() =>
  Object.values(props.conversation).filter((m) => m.sender !== ("system" as string)),
);
</script>
