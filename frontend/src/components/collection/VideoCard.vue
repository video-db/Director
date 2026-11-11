<template>
  <div
    class="video-card vdb-c-flex vdb-c-h-full vdb-c-cursor-pointer vdb-c-flex-col vdb-c-rounded-lg vdb-c-bg-kilvish-200 vdb-c-p-6 vdb-c-transition-colors vdb-c-duration-300 hover:vdb-c-bg-white hover:vdb-c-shadow-lg"
    @mouseenter="hoveredVideo = item.id"
    @mouseleave="hoveredVideo = null"
  >
    <div
      :class="[
        'vdb-c-flex vdb-c-flex-col sm:vdb-c-block sm:vdb-c-flex-row',
        {
          'vdb-c-mb-14': variant === 'default',
        },
      ]"
    >
      <div
        :class="[
          'sm:vdb-c-min-w-auto sm:vdb-c-min-w-0 vdb-c-w-auto vdb-c-min-w-96 sm:vdb-c-mr-24 sm:vdb-c-w-full',
          {
            'vdb-c-mb-8 sm:vdb-c-mb-16': variant === 'default',
          },
        ]"
      >
        <div v-if="item.stream_url">
          <div>
            <VideoDBPlayer
              :stream-url="item.stream_url"
              :default-controls="false"
              :default-overlay="false"
              class="vdb-c-overflow-hidden vdb-c-rounded-12"
            >
              <template #overlay>
                <BigCenterButton
                  class="vdb-c-absolute vdb-c-left-1/2 vdb-c-top-1/2 vdb-c-flex vdb-c-h-48 vdb-c-w-48 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-bg-black/40 vdb-c-transition-all vdb-c-duration-300 hover:vdb-c-bg-white/40"
                >
                </BigCenterButton>

                <div
                  class="vdb-c-absolute vdb-c-right-4 vdb-c-top-4 vdb-c-rounded-full vdb-c-border vdb-c-bg-black/40 vdb-c-p-6 vdb-c-backdrop-blur vdb-c-transition-transform vdb-c-duration-300 hover:vdb-c-scale-110 hover:vdb-c-bg-white/45"
                  @click="copyId(item.id)"
                >
                  <CopyIcon />
                </div>

                <div
                  class="vdb-c-absolute vdb-c-bottom-4 vdb-c-right-4 vdb-c-rounded-full vdb-c-border vdb-c-bg-black/40 vdb-c-p-6 vdb-c-backdrop-blur vdb-c-transition-transform vdb-c-duration-300 hover:vdb-c-scale-110 hover:vdb-c-bg-white/50"
                  @click="$emit('video-click', item)"
                >
                  <ExternalLinkIcon v-if="item.stream_url" />
                </div>
              </template>
            </VideoDBPlayer>
          </div>
        </div>
        <div
          v-else
          class="vid-pb vdb-c-relative vdb-c-overflow-hidden vdb-c-rounded-[7px]"
        >
          <div
            v-if="item.thumbnail_url"
            class="thumbnail vdb-c-absolute vdb-c-bottom-0 vdb-c-left-0 vdb-c-right-0 vdb-c-top-0 vdb-c-h-106 vdb-c-rounded-lg vdb-c-bg-cover vdb-c-bg-center vdb-c-bg-no-repeat vdb-c-shadow-1"
            :style="{
              backgroundImage: `url('${item.thumbnail_url}')`,
              backgroundColor: 'transparent',
            }"
            @click="$emit('video-click', item)"
          ></div>
          <default-thumbnail
            v-else
            class="thumbnail vdb-c-absolute vdb-c-bottom-0 vdb-c-left-0 vdb-c-right-0 vdb-c-top-0 vdb-c-h-106 vdb-c-animate-pulse vdb-c-rounded-lg vdb-c-bg-cover vdb-c-bg-center vdb-c-bg-no-repeat vdb-c-shadow-1"
            @click="$emit('video-click', item)"
          />
          <div
            class="center-button transparent-button vdb-c-absolute vdb-c-left-1/2 vdb-c-top-1/2 vdb-c-flex vdb-c-h-48 vdb-c-w-48 -vdb-c-translate-x-1/2 -vdb-c-translate-y-1/2 vdb-c-transform vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full lg:vdb-c-h-56 lg:vdb-c-w-56"
            @click="$emit('video-click', item)"
          >
            <PlayIcon class="vdb-c-h-20 vdb-c-w-20" />
          </div>
        </div>
      </div>
      <div
        v-if="variant === 'default'"
        class="vdb-c-mx-8 vdb-c-mb-8 vdb-c-flex vdb-c-items-center vdb-c-justify-between vdb-c-text-kilvish-900"
        @click="$emit('video-click', item)"
      >
        <p
          class="text-elip vdb-c-mb-0 vdb-c-line-clamp-2 vdb-c-whitespace-normal vdb-c-text-xs vdb-c-font-medium"
        >
          {{ item.name }}
        </p>
        <!-- Delete Icon -->
        <span
          class="vdb-c-ml-4 vdb-c-cursor-pointer vdb-c-transition-all vdb-c-duration-300 hover:vdb-c-scale-110"
          @mouseenter="hoveredDeleteIcon = item.id"
          @mouseleave="hoveredDeleteIcon = null"
          @click.stop="$emit('delete-video', item)"
        >
          <DeleteIcon
            :fill="hoveredDeleteIcon === item.id ? '#EC5B16' : '#CCCCCC'"
          />
        </span>
      </div>
    </div>
  </div>
  <NotificationCenter ref="notificationCenterRef" />
</template>

<script setup>
import { BigCenterButton, VideoDBPlayer } from "@videodb/player-vue";
import "@videodb/player-vue/dist/style.css";
import { ref } from "vue";
import DefaultThumbnail from "../assets/DefaultThumbnail.vue";
import NotificationCenter from "../chat/elements/NotificationCenter.vue";
import DeleteIcon from "../icons/Delete2.vue";
import PlayIcon from "../icons/play.vue";

import CopyIcon from "../icons/CopyIcon.vue";
import ExternalLinkIcon from "../icons/ExternalLink.vue";

const hoveredVideo = ref(null);
const hoveredDeleteIcon = ref(null);

const props = defineProps({
  item: {
    type: Object,
    default: () => ({}),
  },
  index: {
    type: Number,
    default: 0,
  },
  variant: {
    type: String,
    default: "default",
  },
});

const secondsToHHMMSS = (val) => {
  if (!val) return "00:00:00";
  let time = "";
  time = new Date(val * 1000).toISOString().substring(11, 19);
  if (time.substring(0, 2) === "00") {
    return time.substring(3, time.length);
  }
  return time;
};

const notificationCenterRef = ref(null);

function copyId(id) {
  navigator.clipboard
    .writeText(id)
    .then(() => {
      notificationCenterRef.value.addNotification("Video ID Copied");
    })
    .catch((e) => {
      print(e);
      notificationCenterRef.value.addNotification("Failed to copy ID");
    });
}

const emit = defineEmits(["delete-video"]);
</script>

<style scoped>
.transparent-button {
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.24);
  backdrop-filter: blur(16px);
  color: #fff;
  opacity: 0;
}

.vid-pb {
  padding-bottom: 56.25%;
}

.text-elip {
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.center-button,
.fade-on-hover {
  transition: all 0.3s ease-in-out;
}
.thumbnail {
  transition: transform 0.5s linear;
  transform-origin: center;
  transform: scale(1.001);
}
@media (max-width: 640px) {
  .thumbnail {
    height: 106px;
  }
  .vid-pb {
    padding-bottom: 40%;
  }
}

@media (any-hover: hover) {
  .video-card:hover .center-button {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.05);
    background: rgba(0, 0, 0, 0.32);
    transform-origin: center;
  }
  .video-card:hover .fade-on-hover {
    opacity: 0.6;
  }
  .video-card:hover .thumbnail {
    transform: scale(1.05);
  }
}
</style>
