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
      <div v-if="content.status === 'success' || content.status === 'progress'">
        <VideoList
          :columns="columns"
          :show-pagination="false"
          :asset-results="content.videos"
          @video-click="handleVideoClick"
        />
      </div>
      <div
        v-else-if="content.status === 'not_generated'"
        class="vdb-c-flex vdb-c-flex-col"
      ></div>
    </transition>
  </div>
</template>

<script setup>
import "@videodb/player-vue/dist/style.css";
import { computed, ref } from "vue";
import { useChatActions } from "@/composables/useChatActions";
import VideoList from "../collection/VideoList.vue";
import LoadingMessage from "./elements/LoadingMessage.vue";

const { send } = useChatActions();
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

const columns = computed(() => props.content?.ui_config?.columns || 4);

const isFullScreen = ref(false);

const handleFullScreenChange = () => {
  isFullScreen.value = !isFullScreen.value;
  if (isFullScreen.value) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
};

const handleVideoClick = (video) => {
  if (video.external_url) {
    window.open(video.external_url, "_blank");
  } else {
    if (video.stream_url) {
      handleAddMessage(`@stream_video ${video.name}`);
    }
  }
};

const handleAddMessage = (text) => {
  send({ text });
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
