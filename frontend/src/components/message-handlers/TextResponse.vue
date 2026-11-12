<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    class="vdb-c-relative vdb-c-flex vdb-c-w-full vdb-c-flex-col vdb-c-gap-8 vdb-c-bg-white vdb-c-py-14 vdb-c-text-left"
  >
    <LoadingMessage
      v-if="!isUser && !isInterimText"
      :status="
        isMainReponse && message.status === 'error' ? 'error' : content.status
      "
      :message="content?.status_message"
      :is-focused="isMainReponse"
      :is-last-conv="isLastConv"
    />

    <transition name="fade" mode="out-in">
      <div
        v-if="
          content.status === 'success' || content.status === 'error' || isUser
        "
        class="vdb-c-flex vdb-c-flex-col"
      >
        <p
          :class="[
            'markdown-body vdb-c-overflow-hidden vdb-c-text-kilvish-900',
            isUser ? 'vdb-c-font-semibold' : 'vdb-c-font-normal',
          ]"
          v-html="getMarkedMsg(text)"
        ></p>
      </div>
      <div
        v-else-if="content.status === 'progress'"
        class="vdb-c-flex-start vdb-c-flex vdb-c-flex-col"
      >
        <div
          class="vdb-c-mb-2 vdb-c-h-16 vdb-c-w-3/4 vdb-c-animate-pulse vdb-c-rounded vdb-c-bg-gray-200"
        ></div>
        <div
          class="vdb-c-mb-2 vdb-c-h-16 vdb-c-w-1/2 vdb-c-animate-pulse vdb-c-rounded vdb-c-bg-gray-200"
        ></div>
        <div
          class="vdb-c-h-16 vdb-c-w-2/3 vdb-c-animate-pulse vdb-c-rounded vdb-c-bg-gray-200"
        ></div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, watch } from "vue";
import Prism from "prismjs";
import { marked } from "marked";
import markedKatex from "marked-katex-extension";
import "prismjs/themes/prism.css";
import "prismjs/components/prism-python"
import LoadingMessage from "./elements/LoadingMessage.vue";
import { useChatStore } from "@/stores/chat";
const options = {
  nonStandard: true,
};

const props = defineProps({
  content: {
    type: Object,
    required: true,
  },
  isUser: {
    type: Boolean,
    default: false,
  },
  mediaTypesObject: {
    type: Object,
    default: () => ({}),
  },
  isLastConv: {
    type: Boolean,
    default: false,
  },
  convId: {
    type: String,
    default: "",
  },
  msgId: {
    type: String,
    default: "",
  },
});

const text = computed(() => props.content?.text || "");
const { conversations } = useChatStore();

marked.setOptions({
  highlight: function (code, lang) {
    if (Prism.languages[lang]) {
      return Prism.highlight(code, Prism.languages[lang], lang);
    }
    return code; // Fallback
  },
});

const getMarkedMsg = (msg) => {
  marked.use(markedKatex(options));
  return marked.parse(msg);
};

const message = computed(() => {
  return conversations?.[props.convId]?.[props.msgId];
});

// The model's text before a tool call is narration; only its last text, once
// the turn is done, is the reply.
const isMainReponse = computed(() => {
  if (props.content.agent_name !== "assistant") return false;
  if (message.value?.status === "progress") return false;
  const texts = (message.value?.content ?? []).filter(
    (c) => c.agent_name === "assistant",
  );
  return texts.length === 0 || texts[texts.length - 1] === props.content;
});
const isInterimText = computed(
  () => props.content.agent_name === "assistant" && !isMainReponse.value,
);
</script>

<style>
.vdb-c-readMoreGradient {
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.3) 0%,
    rgba(255, 255, 255, 1) 100%
  );
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
