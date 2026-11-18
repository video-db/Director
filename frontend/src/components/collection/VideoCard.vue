<template>
  <!-- Same shape as the library's MediaThumbnail, with the player inline. -->
  <div class="flex w-full flex-col gap-8 rounded-md p-12 transition-colors hover:bg-background-neutral-hover">
    <div class="relative aspect-video w-full overflow-hidden rounded-sm bg-background-neutral-inverse-secondary">
      <VideoDBPlayer
        v-if="video.stream_url"
        class="size-full"
        :stream-url="video.stream_url"
        :default-controls="false"
        :default-overlay="false"
      >
        <template #overlay>
          <BigCenterButton class="absolute top-1/2 left-1/2 size-48" />
        </template>
      </VideoDBPlayer>
      <img v-else-if="video.thumbnail_url" :src="video.thumbnail_url" alt="" class="size-full object-cover" />
    </div>
    <div class="flex flex-col">
      <p class="truncate text-sm text-text-neutral-primary" :title="video.name">{{ video.name || "Untitled video" }}</p>
      <div class="flex items-center gap-4">
        <p class="flex-1 text-xs text-text-neutral-tertiary">{{ video.length ? formatDuration(video.length) : "" }}</p>
        <IconButton v-if="video.id" icon="content_copy" label="Copy video ID" size="xs" @click="copyId" />
        <IconButton v-if="canOpen" icon="open_in_new" label="Open video" size="xs" @click="openVideo(video as Video)" />
        <IconButton v-if="deletable" icon="delete" label="Delete video" size="xs" @click="emit('delete', video as Video)" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BigCenterButton, VideoDBPlayer } from "@videodb/player-vue";
import { computed } from "vue";

import { formatDuration } from "@/components/ui/duration-label";
import { IconButton } from "@/components/ui/icon-button";
import { useToast } from "@/components/ui/toast";
import { useOpenVideo } from "@/composables/useOpenVideo";
import type { Video } from "@/types";

const props = defineProps<{ video: Partial<Video>; deletable?: boolean }>();
const emit = defineEmits<{ delete: [Video] }>();

const { toast } = useToast();
const openVideo = useOpenVideo();

const canOpen = computed(() => !!props.video.external_url || !!(props.video.id && props.video.collection_id));

async function copyId() {
  try {
    await navigator.clipboard.writeText(props.video.id!);
    toast.success("Copied the video ID");
  } catch {
    toast.error("Couldn't copy the video ID");
  }
}
</script>
