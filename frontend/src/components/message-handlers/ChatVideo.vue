<template>
  <div class="flex w-full flex-col gap-12 text-left">
    <LoadingMessage :status="content.status ?? 'progress'" :message="content.status_message" />

    <div v-if="content.status === 'success' && video?.stream_url" class="flex w-full max-w-xl flex-col gap-8">
      <div
        ref="frame"
        :class="
          isFullScreen
            ? 'flex size-full items-center justify-center bg-background-neutral-inverse-primary'
            : 'overflow-hidden rounded-md border border-border-neutral-primary'
        "
      >
        <VideoDBPlayer
          :class="isFullScreen ? 'size-full' : ''"
          :stream-url="video.stream_url"
          :default-controls="false"
          :default-overlay="false"
          @full-screen-change="toggleFullScreen"
        >
          <template #overlay>
            <BigCenterButton class="absolute top-1/2 left-1/2 size-48" />
          </template>
          <template #controls>
            <div class="flex flex-col gap-8 p-16">
              <ProgressBar :stream-url="video.stream_url" />
              <div class="flex w-full items-center justify-between">
                <div class="z-10 flex items-center">
                  <PlayPauseButton />
                  <VolumeControlButton />
                  <TimeCode />
                </div>
                <FullScreenButton />
              </div>
            </div>
          </template>
        </VideoDBPlayer>
      </div>

      <div v-if="video.name || canOpen" class="flex items-center gap-8">
        <div class="flex min-w-0 flex-1 flex-col gap-2">
          <p class="truncate text-sm font-medium text-text-neutral-primary">{{ video.name || "Untitled video" }}</p>
          <p v-if="video.length" class="text-xs text-text-neutral-tertiary">{{ formatDuration(video.length) }}</p>
        </div>
        <IconButton v-if="video.id" icon="content_copy" label="Copy video ID" size="sm" @click="copyId" />
        <IconButton v-if="canOpen" icon="open_in_new" label="Open video" size="sm" @click="open" />
      </div>
    </div>

    <Skeleton v-else-if="content.status === 'progress'" class="aspect-video w-full max-w-xl rounded-md" />
  </div>
</template>

<script setup lang="ts">

import {
  BigCenterButton,
  FullScreenButton,
  PlayPauseButton,
  ProgressBar,
  TimeCode,
  VideoDBPlayer,
  VolumeControlButton,
} from "@videodb/player-vue";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import { formatDuration } from "@/components/ui/duration-label";
import { IconButton } from "@/components/ui/icon-button";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useOpenVideo } from "@/composables/useOpenVideo";
import type { ContentBase, Video } from "@/types";

import LoadingMessage from "./elements/LoadingMessage.vue";

const props = defineProps<{
  content: ContentBase & { video?: Partial<Video> };
  isLastConv?: boolean;
}>();

const { toast } = useToast();
const openVideo = useOpenVideo();

const video = computed(() => props.content.video);
const canOpen = computed(
  () => !!video.value?.external_url || !!(video.value?.id && video.value?.collection_id),
);

function open() {
  if (video.value) openVideo(video.value as Video);
}

async function copyId() {
  try {
    await navigator.clipboard.writeText(video.value?.id ?? "");
    toast.success("Copied the video ID");
  } catch {
    toast.error("Couldn't copy the video ID");
  }
}

// Fullscreen goes on this player's own frame, so other players on the page stay put.
const frame = ref<HTMLElement>();
const isFullScreen = ref(false);

function toggleFullScreen() {
  if (document.fullscreenElement) document.exitFullscreen();
  else frame.value?.requestFullscreen();
}

function onFullScreenChange() {
  isFullScreen.value = !!frame.value && document.fullscreenElement === frame.value;
}

onMounted(() => document.addEventListener("fullscreenchange", onFullScreenChange));
onBeforeUnmount(() => document.removeEventListener("fullscreenchange", onFullScreenChange));
</script>
