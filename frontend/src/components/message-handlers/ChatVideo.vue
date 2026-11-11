<template>
  <div
    class="vdb-c-relative vdb-c-flex vdb-c-w-full vdb-c-flex-col vdb-c-gap-8 vdb-c-py-14 vdb-c-text-left"
  >
    <LoadingMessage
      :status="content.status"
      :message="content.status_message"
      :is-last-conv="isLastConv"
    />
    <transition name="fade" mode="out-in">
      <div
        v-if="content.status === 'success' && content.video.stream_url"
        class="vdb-c-w-full vdb-c-py-6"
      >
        <div
          :class="
            isFullScreen
              ? 'vdb-c-fixed vdb-c-inset-0 vdb-c-z-50 vdb-c-flex vdb-c-h-full vdb-c-w-full vdb-c-flex-col vdb-c-items-center vdb-c-justify-center vdb-c-overflow-y-hidden vdb-c-bg-black-64'
              : 'vdb-c-full xl:vdb-c-1/2 vdb-c-overflow-hidden vdb-c-rounded-20 sm:vdb-c-w-3/4 lg:vdb-c-w-3/5 xl:vdb-c-w-1/2'
          "
        >
          <VideoDBPlayer
            :class="isFullScreen ? 'vdb-c-h-screen vdb-c-w-screen' : ''"
            :stream-url="content.video.stream_url"
            :default-controls="false"
            :default-overlay="false"
            @fullScreenChange="handleFullScreenChange"
          >
            <template #overlay>
              <BigCenterButton
                class="vdb-c-absolute vdb-c-left-1/2 vdb-c-top-1/2 vdb-c-h-32 vdb-c-w-32 md:vdb-c-h-48 md:vdb-c-w-48"
              />
            </template>
            <template #controls>
              <div class="vdb-p-pt-0 vdb-c-p-20">
                <div class="sm:vdb-p-mx-8 vdb-c-mb-8 md:vdb-c-mb-12">
                  <ProgressBar :stream-url="content.video.stream_url" />
                </div>
                <div class="vdb-c-flex vdb-c-w-full vdb-c-justify-between">
                  <div
                    class="vdb-c-z-10 vdb-c-ml-0 vdb-c-flex vdb-c-items-center"
                  >
                    <PlayPauseButton />
                    <VolumeControlButton />
                    <TimeCode />
                  </div>

                  <FullScreenButton class="" />
                </div>
              </div>
            </template>
          </VideoDBPlayer>
        </div>
      </div>
      <div v-else-if="content.status === 'progress'">
        <div
          class="vdb-c-full xl:vdb-c-1/2 vdb-c-animate-pulse vdb-c-overflow-hidden vdb-c-rounded-20 sm:vdb-c-w-3/4 lg:vdb-c-w-3/5 xl:vdb-c-w-1/2"
        >
          <div class="vdb-c-relative vdb-c-w-full" style="padding-top: 56.25%">
            <div
              class="vdb-c-absolute vdb-c-inset-0 vdb-c-flex vdb-c-items-center vdb-c-justify-center vdb-c-bg-gray-200"
            ></div>
          </div>
        </div>
      </div>
      <div
        v-else-if="content.status === 'not_generated'"
        class="vdb-c-flex vdb-c-flex-col"
      ></div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from "vue";
import {
  VideoDBPlayer,
  TimeCode,
  BigCenterButton,
  VolumeControlButton,
  PlayPauseButton,
  FullScreenButton,
  ProgressBar,
} from "@videodb/player-vue";
import "@videodb/player-vue/dist/style.css";
import LoadingMessage from "./elements/LoadingMessage.vue";

const props = defineProps({
  content: {
    type: Object,
    required: true,
  },
  isLastConv: {
    type: Boolean,
    default: false,
  },
});

const isFullScreen = ref(false);

const handleFullScreenChange = () => {
  isFullScreen.value = !isFullScreen.value;
  if (isFullScreen.value) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
};
</script>

<style lang="scss">
.video-js .vjs-big-play-button {
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
