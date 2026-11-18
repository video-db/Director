<template>
  <Marker :role="status === 'progress' ? 'status' : undefined">
    <MarkerIcon>
      <Spinner v-if="status === 'progress'" size="sm" decorative />
      <Icon
        v-else-if="status === 'success'"
        name="check_circle"
        filled
        :size="16"
        :class="isFocused ? 'text-icon-success-primary' : 'text-icon-neutral-tertiary'"
      />
      <Icon v-else name="error" filled :size="16" class="text-icon-error-primary" />
    </MarkerIcon>
    <MarkerContent
      :shimmer="status === 'progress'"
      :class="{
        'font-medium text-text-neutral-primary': status === 'success' && isFocused,
        'text-text-error-primary': status === 'error',
      }"
    >
      {{ text }}
    </MarkerContent>
  </Marker>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { Icon } from "@/components/ui/icon";
import { Marker, MarkerContent, MarkerIcon } from "@/components/ui/marker";
import { Spinner } from "@/components/ui/spinner";

const props = defineProps<{
  status: "progress" | "success" | "error" | string;
  message?: string;
  isFocused?: boolean;
}>();

const text = computed(() => {
  if (props.message) return props.message;
  if (props.status === "progress") return "Thinking…";
  if (props.status === "error") return "Something went wrong";
  return "Here is your response";
});
</script>
