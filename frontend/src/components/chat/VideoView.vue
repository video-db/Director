<template>
  <div class="w-full">
    <div v-if="videoData" class="w-full overflow-hidden rounded-md bg-black shadow-xs">
      <div :class="isFullScreen ? 'fixed inset-0 z-50 flex flex-col items-center justify-center bg-black' : 'w-full'">
        <VideoDBPlayer
          :class="isFullScreen ? 'h-screen w-screen' : ''"
          :stream-url="videoData.stream_url"
          :default-overlay="false"
          @full-screen-change="isFullScreen = !isFullScreen"
        >
          <template #overlay>
            <BigCenterButton class="absolute top-1/2 left-1/2" />
          </template>
        </VideoDBPlayer>
      </div>
    </div>
    <Skeleton v-else class="aspect-video w-full rounded-md" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { BigCenterButton, VideoDBPlayer } from "@videodb/player-vue";

import { Skeleton } from "@/components/ui/skeleton";
import type { Collection, Video } from "@/types";

defineProps<{
  collectionId: string;
  videoId: string;
  collectionData?: Collection;
  videoData?: Video;
}>();

const isFullScreen = ref(false);
</script>
