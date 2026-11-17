<!-- eslint-disable vue/no-v-html -->
<template>
  <div class="vdb-c-py-8 vdb-c-text-left">
    <div class="vdb-c-rounded-12 vdb-c-bg-kilvish-100 vdb-c-p-16">
      <p
        class="vdb-c-text-subheader vdb-c-font-semibold vdb-c-text-kilvish-900"
      >
        {{ title }}
      </p>
      <!-- Reasons can come from the safety check's LLM, so they're rendered as text, never HTML. -->
      <p
        v-if="content.reason"
        class="vdb-c-mt-4 vdb-c-text-body vdb-c-text-kilvish-700"
      >
        <template v-for="(part, i) in reasonParts" :key="i">
          <code
            v-if="i % 2"
            class="vdb-c-rounded-4 vdb-c-bg-kilvish-200 vdb-c-px-4"
            >{{ part }}</code
          >
          <template v-else>{{ part }}</template>
        </template>
      </p>

      <div
        class="markdown-body approval-preview vdb-c-mt-12 vdb-c-overflow-hidden"
        v-html="previewHtml"
      ></div>

      <div v-if="content.state === 'pending'" class="vdb-c-mt-12">
        <div
          v-if="!denying"
          class="vdb-c-flex vdb-c-flex-wrap vdb-c-items-center vdb-c-gap-16"
        >
          <Button variant="primary" @click="answer('once')">Allow once</Button>
          <button
            v-if="content.options.includes('chat')"
            class="vdb-c-text-subheader vdb-c-font-medium vdb-c-text-kilvish-900 hover:vdb-c-underline"
            @click="answer('chat')"
          >
            Allow for this chat
          </button>
          <button
            class="vdb-c-text-subheader vdb-c-font-medium vdb-c-text-red-dark hover:vdb-c-underline"
            @click="denying = true"
          >
            Deny
          </button>
        </div>

        <form
          v-else
          class="vdb-c-flex vdb-c-flex-wrap vdb-c-items-center vdb-c-gap-12"
          @submit.prevent="answer('deny', note)"
        >
          <input
            ref="noteRef"
            v-model="note"
            type="text"
            maxlength="2000"
            placeholder="What should Director do instead? (optional)"
            class="vdb-c-min-w-[0] vdb-c-flex-1 vdb-c-rounded-8 vdb-c-border vdb-c-border-kilvish-400 vdb-c-bg-white vdb-c-px-12 vdb-c-py-8 vdb-c-text-body vdb-c-text-kilvish-900 vdb-c-outline-none focus:vdb-c-border-kilvish-600"
          />
          <Button variant="primary" type="submit">Deny</Button>
          <button
            type="button"
            class="vdb-c-text-subheader vdb-c-font-medium vdb-c-text-kilvish-700 hover:vdb-c-underline"
            @click="denying = false"
          >
            Cancel
          </button>
        </form>
      </div>

      <p v-else class="vdb-c-mt-12 vdb-c-text-body" :class="stateClass">
        {{ stateText }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import Prism from "prismjs";
import "prismjs/components/prism-python";
import "prismjs/components/prism-bash";

import Button from "@/components/buttons/Button.vue";
import { useChatStore } from "@/stores/chat";
import type { ApprovalContent, ApprovalDecision } from "@/types";

const props = defineProps<{
  content: ApprovalContent;
  convId?: string;
  msgId?: string;
}>();

const chat = useChatStore();
const denying = ref(false);
const note = ref("");
const noteRef = ref<HTMLInputElement | null>(null);

watch(denying, async (open) => {
  if (open) {
    await nextTick();
    noteRef.value?.focus();
  }
});

const TOOL_NAMES: Record<string, string> = {
  code_executor: "run Python",
  bash_executor: "run a command",
};

const title = computed(
  () =>
    `Director wants to ${TOOL_NAMES[props.content.agent_name ?? ""] ?? `use ${props.content.agent_name}`}`,
);

const previewHtml = computed(() => {
  const lang = props.content.language;
  const grammar = Prism.languages[lang];
  const code = grammar
    ? Prism.highlight(props.content.preview, grammar, lang)
    : escapeHtml(props.content.preview);
  return `<pre class="language-${lang}"><code class="language-${lang}">${code}</code></pre>`;
});

// Odd parts were inside `backticks`.
const reasonParts = computed(() => props.content.reason.split("`"));

const stateText = computed(() => {
  const { state, decided_by, note: savedNote } = props.content;
  switch (state) {
    case "sending":
      return "Sending your answer…";
    case "running":
      return `${decided_by ?? "Approved"}. Running…`;
    case "approved":
      return decided_by ?? "Approved";
    case "denied":
      return savedNote
        ? `${decided_by ?? "Denied"}: “${savedNote}”`
        : (decided_by ?? "Denied");
    case "skipped":
      return "Skipped: you sent a new message";
    case "interrupted":
      return "Interrupted before it finished";
    default:
      return "";
  }
});

const stateClass = computed(() =>
  props.content.state === "denied"
    ? "vdb-c-text-red-dark"
    : "vdb-c-text-kilvish-700",
);

function answer(decision: ApprovalDecision, text?: string) {
  const message = chat.conversations[props.convId ?? ""]?.[props.msgId ?? ""];
  if (!message) return;
  chat.answerApproval(message, props.content, decision, text?.trim());
  denying.value = false;
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
</script>

<style>
.approval-preview pre {
  margin: 0;
  max-height: 320px;
  overflow: auto;
}
</style>
