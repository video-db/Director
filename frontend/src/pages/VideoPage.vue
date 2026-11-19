<template>
  <div class="mx-auto flex w-full max-w-760 flex-col gap-16 px-16 py-24 md:px-24">
    <VideoView
      :collection-id="collectionId"
      :video-id="videoId"
      :collection-data="collections.activeCollection ?? undefined"
      :video-data="video ?? undefined"
    />

    <div v-if="video" class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-12">
        <h1 class="min-w-0 text-lg font-semibold break-words text-text-neutral-primary">
          {{ video.name }}
        </h1>
        <Badge v-if="video.length" colour="neutral" size="sm" class="shrink-0 tabular-nums">
          {{ formatDuration(video.length) }}
        </Badge>
      </div>
      <p class="text-sm text-text-neutral-tertiary">Ask Director anything about this video below.</p>
    </div>
    <div v-else role="status" aria-label="Loading video" class="flex flex-col gap-8">
      <Skeleton class="h-24 w-1/2 rounded-xs" />
      <Skeleton class="h-16 w-2/3 rounded-xs" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute } from "vue-router";

import VideoView from "@/components/chat/VideoView.vue";
import { Badge } from "@/components/ui/badge";
import { formatDuration } from "@/components/ui/duration-label";
import { Skeleton } from "@/components/ui/skeleton";
import { useChatStore } from "@/stores/chat";
import { useCollectionsStore } from "@/stores/collections";

const route = useRoute();
const chat = useChatStore();
const collections = useCollectionsStore();

const collectionId = computed(() => route.params.collectionId as string);
const videoId = computed(() => route.params.videoId as string);
const video = computed(() => collections.activeVideo);

// Messages sent from here start a session about this video.
watch(
  [collectionId, videoId],
  ([cid, vid]) => {
    chat.reset();
    chat.videoId = vid;
    collections.setActive(cid);
  },
  { immediate: true },
);
</script>
