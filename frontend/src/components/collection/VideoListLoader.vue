<template>
  <div
    role="status"
    aria-label="Loading media"
    class="grid grid-cols-1 gap-16 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
  >
    <div v-for="n in count" :key="n" class="flex flex-col gap-8">
      <Skeleton class="aspect-video w-full rounded-sm" />
      <Skeleton class="h-16 w-3/4 rounded-xs" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Skeleton } from "@/components/ui/skeleton";

withDefaults(defineProps<{ count?: number }>(), { count: 8 });
</script>
