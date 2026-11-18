<template>
  <!-- The user's message: a bubble on the right. -->
  <div v-if="isUser" class="flex w-full flex-col items-end gap-8">
    <ImageHandler
      v-if="image"
      :content="image"
      :is-user="true"
      :conv-id="message.conv_id"
      :msg-id="message.msg_id"
    />
    <div
      v-if="text"
      class="max-w-[85%] rounded-md rounded-br-xxs bg-background-neutral-secondary px-16 py-10 text-md text-text-neutral-primary"
    >
      <TextResponse :content="text" :is-user="true" :conv-id="message.conv_id" :msg-id="message.msg_id" />
    </div>
  </div>

  <!-- Director's reply: its log, then each piece of content. -->
  <div v-else-if="isAssistant" class="flex w-full flex-col gap-16">
    <ChatMessageSteps
      :steps="message.actions ?? []"
      :status="finalStatus"
      :expanded="isLastConv && message.status !== 'success'"
    />
    <template v-for="(content, i) in message.content ?? []" :key="i">
      <component
        :is="messageRenderers[content.type]"
        v-if="messageRenderers[content.type]"
        :is-last-conv="isLastConv"
        :content="content"
        :is-user="false"
        :search-term="searchTerm"
        :conv-id="message.conv_id"
        :msg-id="message.msg_id"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import ImageHandler from "@/components/message-handlers/ImageHandler.vue";
import TextResponse from "@/components/message-handlers/TextResponse.vue";
import { messageRenderers } from "@/messageRenderers";
import type { Message } from "@/types";

import ChatMessageSteps from "./elements/ChatMessageSteps.vue";

const props = defineProps<{
  message: Message;
  isLastConv?: boolean;
  searchTerm?: string;
}>();

const isUser = computed(() => props.message.msg_type === "input");
const isAssistant = computed(() => props.message.msg_type === "output");
const image = computed(() => props.message.content?.find((c) => c.type === "image"));
const text = computed(() => props.message.content?.find((c) => c.type === "text"));

const finalStatus = computed(() => {
  const status = props.message.status as string | undefined;
  if (status === "error" || status === "awaiting_approval") return status;
  const assistant = props.message.content?.find((c) => c.agent_name === "assistant");
  return assistant?.status || props.message.status || "progress";
});
</script>
