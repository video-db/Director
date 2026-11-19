<template>
  <Card size="sm">
    <CardHeader>
      <div class="flex items-center gap-12">
        <span
          class="flex size-32 shrink-0 items-center justify-center rounded-xs border border-border-neutral-primary bg-background-neutral-subtle"
        >
          <Icon :name="icon" :size="16" class="text-icon-neutral-secondary" />
        </span>
        <CardTitle as="h2">{{ title }}</CardTitle>
      </div>
      <CardAction>
        <Badge
          :colour="configured ? 'success' : 'error'"
          emphasis="subtle"
          size="sm"
          :icon="configured ? 'check_circle' : 'error'"
        >
          {{ configured ? "Configured" : "Missing" }}
        </Badge>
      </CardAction>
    </CardHeader>
    <CardContent v-if="!configured" class="flex flex-col gap-12">
      <p class="text-sm text-text-neutral-secondary">
        <slot />
      </p>
      <CodeBlock v-if="envLine" :code="envLine" title="backend/.env" />
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Badge } from "@/components/ui/badge";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CodeBlock } from "@/components/ui/code-block";
import { Icon } from "@/components/ui/icon";

// The default slot holds the fix-it instructions, shown only while the item is missing.
defineProps<{
  title: string;
  icon: string;
  configured: boolean;
  /** Line to add to the backend .env, e.g. "VIDEO_DB_API_KEY=" */
  envLine?: string;
}>();
</script>
