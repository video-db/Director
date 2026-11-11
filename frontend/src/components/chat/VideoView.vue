<template>
  <div
    class="vdb-c-relative vdb-c-mx-auto vdb-c-w-full vdb-c-py-28 md:vdb-c-w-5/6 lg:vdb-c-w-4/5 xl:vdb-c-w-3/4"
  >
    <div
      class="vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-justify-center vdb-c-overflow-hidden vdb-c-rounded-xl vdb-c-bg-black"
      v-if="videoData"
    >
      <div
        :class="
          isFullScreen
            ? 'vdb-c-fixed vdb-c-inset-0 vdb-c-z-50 vdb-c-flex vdb-c-h-full vdb-c-w-full vdb-c-flex-col vdb-c-items-center vdb-c-justify-center vdb-c-overflow-y-hidden vdb-c-bg-black-64'
            : 'vdb-c-w-full'
        "
      >
        <VideoDBPlayer
          ref="videoPlayer"
          :class="isFullScreen ? 'vdb-c-h-screen vdb-c-w-screen' : ''"
          :stream-url="videoData?.stream_url"
          :default-overlay="false"
          @fullScreenChange="handleFullScreenChange"
        >
          <template v-slot:overlay>
            <BigCenterButton
              class="vdb-c-absolute vdb-c-left-1/2 vdb-c-top-1/2"
            />
          </template>
        </VideoDBPlayer>
      </div>
    </div>

    <!-- Video Player Loading -->
    <div
      v-else
      class="vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-justify-center vdb-c-rounded-xl vdb-c-bg-roy"
    >
      <div
        class="vdb-c-aspect-video vdb-c-h-full vdb-c-w-full vdb-c-animate-pulse"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { VideoDBPlayer, BigCenterButton } from "@videodb/player-vue";
import "@videodb/player-vue/dist/style.css";

const props = defineProps({
  collectionId: {
    type: String,
    required: true,
  },
  videoId: {
    type: String,
    required: true,
  },
  collectionData: {
    type: Object,
    default: null,
  },
  videoData: {
    type: Object,
    default: null,
  },
});

const isFullScreen = ref(false);

const handleFullScreenChange = () => {
  isFullScreen.value = !isFullScreen.value;
};
</script>

<style scoped></style>
