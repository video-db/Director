<template>
  <div class="flex flex-col gap-24">
    <div :class="['-mx-12 grid gap-y-4', gridClasses[columns] ?? gridClasses[4]]">
      <MediaCard
        v-for="item in pageItems"
        :key="item.id"
        :item="item"
        @open="emit('video-click', $event)"
        @delete="emit('delete', $event)"
      />
    </div>

    <Pagination
      v-if="showPagination && assetResults.length > itemsPerPage"
      v-model:page="page"
      :total="assetResults.length"
      :items-per-page="itemsPerPage"
      label="Media pages"
      class="self-center"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import MediaCard from "@/components/collection/MediaCard.vue";
import { Pagination } from "@/components/ui/pagination";
import type { Media, Video } from "@/types";

type Item = InstanceType<typeof MediaCard>["$props"]["item"];

const props = withDefaults(
  defineProps<{
    assetResults?: Item[];
    itemsPerPage?: number;
    showPagination?: boolean;
    /** Max columns at the widest breakpoint (1–4) */
    columns?: 1 | 2 | 3 | 4;
  }>(),
  { assetResults: () => [], itemsPerPage: 8, showPagination: true, columns: 4 },
);

const emit = defineEmits<{ "video-click": [Video]; delete: [Media] }>();

const gridClasses: Record<number, string> = {
  1: "grid-cols-1",
  2: "grid-cols-1 sm:grid-cols-2",
  3: "grid-cols-1 sm:grid-cols-2 md:grid-cols-3",
  4: "grid-cols-2 md:grid-cols-3 lg:grid-cols-4",
};

const page = ref(1);
// A new filter or search starts back on page 1.
watch(() => props.assetResults, () => (page.value = 1));

const pageItems = computed(() => {
  if (!props.showPagination) return props.assetResults;
  const start = (page.value - 1) * props.itemsPerPage;
  return props.assetResults.slice(start, start + props.itemsPerPage);
});
</script>
