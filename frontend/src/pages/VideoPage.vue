<template>
  <div class="vdb-c-flex vdb-c-w-full vdb-c-flex-col vdb-c-items-center">
    <VideoView
      :collection-id="collectionId"
      :video-id="videoId"
      :collection-data="collections.activeCollection ?? undefined"
      :video-data="collections.activeVideo ?? undefined"
    />
    <p
      v-if="!collections.activeVideo"
      class="vdb-c-py-28 vdb-c-text-sm vdb-c-text-vdb-darkishgrey"
    >
      Loading video…
    </p>
    <p v-else class="vdb-c-pb-16 vdb-c-text-sm vdb-c-text-vdb-darkishgrey">
      Ask Director anything about
      <span class="vdb-c-font-semibold">{{
        collections.activeVideo.name
      }}</span>
      below.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute } from "vue-router";

import VideoView from "@/components/chat/VideoView.vue";
import { useChatStore } from "@/stores/chat";
import { useCollectionsStore } from "@/stores/collections";

const route = useRoute();
const chat = useChatStore();
const collections = useCollectionsStore();

const collectionId = computed(() => route.params.collectionId as string);
const videoId = computed(() => route.params.videoId as string);

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
