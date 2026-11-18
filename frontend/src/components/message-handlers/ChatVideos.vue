<template>
  <div class="@container flex w-full flex-col gap-12 text-left">
    <LoadingMessage :status="content.status ?? 'progress'" :message="content.status_message" />

    <div v-if="videos.length && (content.status === 'success' || content.status === 'progress')" class="-mx-12" :class="gridClass">
      <VideoCard v-for="(video, i) in videos" :key="video.id ?? i" :video="video" />
    </div>

    <div v-else-if="content.status === 'progress'" class="gap-12" :class="gridClass">
      <Skeleton v-for="i in 2" :key="i" class="aspect-video w-full rounded-md" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import VideoCard from "@/components/collection/VideoCard.vue";
import { Skeleton } from "@/components/ui/skeleton";
import type { ContentBase, Video } from "@/types";

import LoadingMessage from "./elements/LoadingMessage.vue";

const props = defineProps<{
  content: ContentBase & { videos?: Partial<Video>[]; ui_config?: { columns?: number } };
  isLastConv?: boolean;
}>();

const videos = computed(() => props.content.videos ?? []);

// ui_config.columns caps the grid; container queries keep cards readable in a narrow chat column.
const gridClass = computed(() => {
  const columns = props.content.ui_config?.columns ?? 4;
  return [
    "grid grid-cols-1",
    columns >= 2 && "@md:grid-cols-2",
    columns >= 3 && "@2xl:grid-cols-3",
    columns >= 4 && "@4xl:grid-cols-4",
  ];
});

</script>
