<template>
  <Drawer v-model:open="open">
    <DrawerContent side="right" class="w-full sm:max-w-640">
      <DrawerHeader>
        <DrawerTitle>{{ title }}</DrawerTitle>
        <DrawerDescription v-if="subtitle">{{ subtitle }}</DrawerDescription>
      </DrawerHeader>

      <div class="min-h-0 flex-1 overflow-y-auto px-24 pb-24">
        <div v-if="loading" class="flex justify-center py-48">
          <Spinner label="Loading the skill" />
        </div>
        <Alert v-else-if="error" status="error">{{ error }}</Alert>
        <template v-else>
          <dl v-if="frontmatter.length" class="mb-16 grid grid-cols-[auto_1fr] gap-x-12 gap-y-4 text-sm">
            <template v-for="[key, value] in frontmatter" :key="key">
              <dt class="font-medium text-text-neutral-secondary">{{ key }}</dt>
              <dd class="min-w-0 break-words text-text-neutral-primary">{{ value }}</dd>
            </template>
          </dl>
          <!-- Sanitised: a SKILL.md comes from whoever published the skill. -->
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div class="markdown-body" v-html="bodyHtml" />
        </template>
      </div>

      <DrawerFooter v-if="$slots.footer">
        <slot name="footer" />
      </DrawerFooter>
    </DrawerContent>
  </Drawer>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { Alert } from "@/components/ui/alert";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import { Spinner } from "@/components/ui/spinner";
import { renderUntrustedMarkdown } from "@/lib/markdown";

const open = defineModel<boolean>("open", { default: false });
const props = defineProps<{
  title: string;
  subtitle?: string;
  content: string;
  loading?: boolean;
  error?: string;
}>();

// The frontmatter is shown as a short table; the rest renders as markdown.
const parts = computed(() => {
  const match = props.content.match(/^---\n([\s\S]*?)\n---\s*\n?/);
  return match
    ? { front: match[1], body: props.content.slice(match[0].length) }
    : { front: "", body: props.content };
});

const frontmatter = computed(() =>
  parts.value.front
    .split("\n")
    .map((line) => line.match(/^([A-Za-z][\w-]*):\s*(.*)$/))
    .filter((m): m is RegExpMatchArray => !!m && !!m[2] && !/^[|>]/.test(m[2]))
    .map((m) => [m[1], m[2].replace(/^["']|["']$/g, "")] as const),
);

const bodyHtml = computed(() => renderUntrustedMarkdown(parts.value.body));
</script>
