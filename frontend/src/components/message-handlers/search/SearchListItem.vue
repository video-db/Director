<template>
  <div>
    <div class="vdb-c-mt-8">
      <div
        v-for="(videoData, index) of searchResults"
        v-show="isExpanded ? true : index === 0"
        :key="`search-results-${index}`"
        class="vdb-c-grid vdb-c-grid-cols-12 vdb-c-gap-18 vdb-c-rounded-20 vdb-c-bg-kilvish-200 vdb-c-p-8 sm:vdb-c-gap-20 sm:vdb-c-p-20"
        :class="`${
          searchResults.length === index + 1 || !isExpanded
            ? 'vdb-c-mb-0'
            : 'vdb-c-mb-20 vdb-c-border-b vdb-c-border-outline-xlight'
        }`"
      >
        <div
          class="vdb-c-space-between vdb-c-col-span-12 vdb-c-flex vdb-c-flex-col vdb-c-gap-12 md:vdb-c-col-span-3"
        >
          <VideoDBPlayer
            :ref="
              (el) => {
                if (el) videoPlayerRefs[index] = el;
              }
            "
            :stream-url="videoData.stream_url"
            :default-controls="false"
            :default-overlay="false"
            class="vdb-c-overflow-hidden vdb-c-rounded-12"
            @play="onPlayPause(index)"
            @pause="onPlayPause(index)"
            @loadeddata="onVideoLoaded(index)"
          >
            <template #overlay>
              <BigCenterButton
                class="vdb-c-absolute vdb-c-left-1/2 vdb-c-top-1/2 vdb-c-w-48 vdb-c-h-48"
                :style="{ height: '48px', width: '48px' }"
              />
            </template>
          </VideoDBPlayer>
          <div
            class="text-elip vdb-c-mb-8 vdb-c-line-clamp-2 vdb-c-whitespace-normal vdb-c-px-8 vdb-c-text-base vdb-c-font-medium vdb-c-text-black"
          >
            {{ videoData.video_title }}
          </div>
        </div>
        <div
          class="vdb-c-col-span-12 vdb-c--mt-20 md:vdb-c-col-span-9 md:vdb-c-mt-0 md:vdb-c-pl-16"
        >
          <div
            class="vdb-c-relative vdb-c-rounded-16 vdb-c-border vdb-c-bg-white vdb-c-text-gray-900"
          >
            <search-results
              v-if="true"
              :is-light="true"
              :on-slide-click="
                (duration) => {
                  onSlideClick(index, duration);
                }
              "
              :search-results="getFormattedSearchResult(videoData)"
              :duration="playerInfo[index]?.duration || 0"
            />
          </div>
        </div>
      </div>
      <div
        v-show="isContractable"
        class="vdb-c-mt-24 vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-justify-center"
      >
        <button
          class="vdb-c-flex vdb-c-cursor-pointer vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-border vdb-c-border-steelblue vdb-c-bg-white vdb-c-px-12 vdb-c-py-8 vdb-c-font-semibold vdb-c-text-steelblue hover:vdb-c-bg-steelblue-200"
          @click="isExpanded = !isExpanded"
        >
          {{ isExpanded ? "See less" : "See more results" }}
          <ChevronDown
            :class-name="`vdb-c-ml-8 ${isExpanded ? 'vdb-c-transform vdb-c-rotate-180' : ''}`"
          />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import ChevronDown from "../../icons/ChevronDown.vue";
import {
  SearchResults,
  VideoDBPlayer,
  BigCenterButton,
} from "@videodb/player-vue";

const props = defineProps({
  searchResults: {
    type: Object,
    default: () => ({}),
  },
  isContractable: {
    type: Boolean,
    default: false,
  },
});

const isExpanded = ref(!props.isContractable);
const videoPlayerRefs = ref({});
const playerInfo = ref({});

const getFormattedSearchResult = (videoData) => {
  const shots = videoData.shots;
  return {
    hits: shots.map((shot, index) => ({
      id: `sr-${index}`,
      start: shot.start,
      text: shot.text,
      end: shot.end,
      type: "relevant",
    })),
  };
};

const onSlideClick = (index, duration) => {
  const player = videoPlayerRefs.value[index];
  if (player) {
    player.seekTo(duration);
    if (!playerInfo.value[index].playing) {
      player.togglePlay();
    }
  }
};
const onPlayPause = (index) => {
  const player = videoPlayerRefs.value[index];
  if (player) {
    playerInfo.value[index] = {
      playing: player.playing,
    };
  }
};
const onVideoLoaded = (index) => {
  const player = videoPlayerRefs.value[index];
  if (player) {
    playerInfo.value[index] = {
      duration: player.duration,
      playing: player.playing,
    };
  }
};
</script>
