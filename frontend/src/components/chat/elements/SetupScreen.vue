<template>
  <div class="flex w-full flex-col gap-24">
    <div class="flex flex-col gap-8">
      <h1 class="text-h5 font-semibold text-text-neutral-primary">Finish setting up Director</h1>
      <p class="text-sm text-text-neutral-secondary">
        {{ missingCount }} of {{ items.length }} {{ missingCount === 1 ? "item needs" : "items need" }}
        attention. Update the backend, restart it, then check again.
      </p>
    </div>

    <div class="flex flex-col gap-12">
      <SetupCard
        v-for="item in items"
        :key="item.key"
        :title="item.title"
        :icon="item.icon"
        :configured="item.configured"
        :env-line="item.envLine"
      >
        <template v-if="item.key === 'videodb_configured'">
          Create an API key in the
          <a
            class="font-medium text-text-brand-primary underline underline-offset-2"
            href="https://console.videodb.ai/keys"
            target="_blank"
            rel="noopener noreferrer"
            >VideoDB console</a
          >
          and add it to the backend <code class="font-mono">.env</code> file.
        </template>
        <template v-else>{{ item.hint }}</template>
      </SetupCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import SetupCard from "@/components/chat/elements/SetupCard.vue";
import type { ConfigStatus } from "@/types";

const props = defineProps<{ configStatus: ConfigStatus }>();

const copy: Record<keyof ConfigStatus, { title: string; icon: string; hint: string; envLine?: string }> = {
  videodb_configured: { title: "VideoDB", icon: "key", hint: "", envLine: "VIDEO_DB_API_KEY=" },
  llm_configured: {
    title: "LLM provider",
    icon: "neurology",
    hint: "Add an LLM key to the backend .env file.",
    envLine: "OPENAI_API_KEY=",
  },
  db_configured: {
    title: "Database",
    icon: "database",
    hint: "Couldn't connect to the database. Check DB_TYPE and its settings in the backend .env file.",
  },
};

const items = computed(() =>
  (Object.keys(copy) as (keyof ConfigStatus)[]).map((key) => ({
    key,
    ...copy[key],
    configured: props.configStatus[key],
  })),
);
const missingCount = computed(() => items.value.filter((i) => !i.configured).length);
</script>
