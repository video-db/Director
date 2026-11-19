<!-- eslint-disable vue/no-v-html -->
<template>
  <Card variant="outline" size="sm" class="text-left">
    <CardContent class="flex flex-col gap-12">
      <div class="flex items-start gap-8">
        <Icon name="shield" :size="20" class="mt-2 shrink-0 text-icon-brand-primary" />
        <div class="flex min-w-0 flex-col gap-4">
          <p class="text-sm font-semibold text-text-neutral-primary">{{ title }}</p>
          <!-- Reasons can come from the safety check's LLM, so they're rendered as text, never HTML. -->
          <p v-if="content.reason" class="text-sm text-text-neutral-secondary">
            <template v-for="(part, i) in reasonParts" :key="i">
              <code v-if="i % 2" class="rounded-xxs bg-background-neutral-secondary px-4 font-mono text-xs">{{ part }}</code>
              <template v-else>{{ part }}</template>
            </template>
          </p>
        </div>
      </div>

      <div class="markdown-body [&_pre]:m-0 [&_pre]:max-h-320" v-html="previewHtml" />

      <template v-if="content.state === 'pending'">
        <div v-if="!denying" class="flex flex-wrap items-center gap-8">
          <Button hierarchy="primary" size="sm" icon="check" @click="answer('once')">Allow once</Button>
          <Button v-if="content.options.includes('chat')" hierarchy="secondary" size="sm" @click="answer('chat')">
            Allow for this chat
          </Button>
          <Button hierarchy="tertiary" size="sm" destructive @click="denying = true">Deny</Button>
        </div>

        <form v-else class="flex flex-wrap items-center gap-8" @submit.prevent="answer('deny', note)">
          <Input
            ref="noteRef"
            v-model="note"
            size="sm"
            maxlength="2000"
            placeholder="What should Director do instead? (optional)"
            aria-label="Note for Director"
            class="min-w-0 flex-1"
          />
          <Button hierarchy="primary" size="sm" destructive type="submit">Deny</Button>
          <Button hierarchy="tertiary" size="sm" type="button" @click="denying = false">Cancel</Button>
        </form>
      </template>

      <Marker v-else>
        <MarkerIcon>
          <Spinner v-if="content.state === 'sending' || content.state === 'running'" size="sm" decorative />
          <Icon v-else :name="stateIcon" :size="16" />
        </MarkerIcon>
        <MarkerContent :class="{ 'text-text-error-primary': content.state === 'denied' }">{{ stateText }}</MarkerContent>
      </Marker>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import Prism from "prismjs";
import "prismjs/components/prism-python";
import "prismjs/components/prism-bash";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Marker, MarkerContent, MarkerIcon } from "@/components/ui/marker";
import { Spinner } from "@/components/ui/spinner";
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
const noteRef = ref<{ $el?: HTMLElement } | null>(null);

watch(denying, async (open) => {
  if (open) {
    await nextTick();
    noteRef.value?.$el?.querySelector("input")?.focus();
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

const stateIcon = computed(() =>
  props.content.state === "approved" ? "check_circle" : props.content.state === "denied" ? "block" : "remove_circle",
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
