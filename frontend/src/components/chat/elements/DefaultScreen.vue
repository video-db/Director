<template>
  <div class="vdb-c-flex vdb-c-flex-col vdb-c-items-center vdb-c-gap-32">
    <!-- Action Cards -->
    <div
      class="fade-in-anim vdb-c-flex vdb-c-grow vdb-c-items-start vdb-c-justify-center vdb-c-pt-4"
    >
      <div
        class="vdb-c-grid vdb-c-grid-cols-1 vdb-c-gap-12 md:vdb-c-grid-cols-3 md:vdb-c-gap-16 2xl:vdb-c-grid-cols-3"
      >
        <div
          v-for="(query, index) in actionCardQueries"
          :key="index"
          :class="[
            'action-card-shadow vdb-c-w-160 vdb-c-h-120 vdb-c-relative vdb-c-flex vdb-c-cursor-pointer vdb-c-flex-col vdb-c-gap-24 vdb-c-rounded-lg vdb-c-border vdb-c-px-12 vdb-c-py-12 vdb-c-transition-all vdb-c-duration-300 vdb-c-ease-in-out md:vdb-c-h-220 md:vdb-c-px-16 md:vdb-c-py-20',
            {
              'vdb-c-border-orange-100 vdb-c-bg-orange-50 hover:vdb-c-border hover:vdb-c-border-[#FFCFA5] hover:vdb-c-bg-[#FFE9D3]':
                query.type === 'primary',
              'vdb-c-border-roy vdb-c-bg-vdb-lightgrey hover:vdb-c-bg-roy':
                query.type === 'muted',
              'vdb-c-bg-orange hover:vdb-c-bg-orange-600': query.type === 'cta',
            },
          ]"
          @click="$emit('query-card-click', query)"
        >
          <div
            v-if="query.isDemo"
            class="vdb-c-absolute vdb-c-right-4 vdb-c-flex vdb-c-flex-row vdb-c-items-center vdb-c-rounded-4 vdb-c-bg-orange-900 vdb-c-px-6 vdb-c-py-3 vdb-c-text-[10px] vdb-c-font-semibold vdb-c-uppercase vdb-c-text-white md:vdb-c-right-12 md:vdb-c-text-xs"
          >
            <span> <StarIcon /> </span>
            <span class="vdb-c-ml-4 vdb-c-hidden md:vdb-c-block"> DEMO </span>
          </div>
          <div
            :class="[
              'vdb-c-hidden vdb-c-h-48 vdb-c-w-48 vdb-c-items-center vdb-c-justify-center vdb-c-self-start vdb-c-rounded-full vdb-c-transition-all vdb-c-duration-300 vdb-c-ease-in-out md:vdb-c-flex',
              {
                'vdb-c-bg-[#B92600A6]': query.type === 'cta',
                'vdb-c-bg-roy': query.type === 'muted',
                'vdb-c-bg-orange-100': query.type === 'primary',
              },
            ]"
          >
            <div
              v-if="query.icon"
              class="vdb-c-flex vdb-c-h-30 vdb-c-w-30 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-bg-orange vdb-c-p-4"
            >
              <component :is="query.icon"> </component>
            </div>
            <QuestionMark
              v-else
              class="query-card-icon"
              :fill="
                query.type === 'cta'
                  ? '#FFFFFF'
                  : query.type === 'muted'
                    ? '#2D2D2D'
                    : '#EC5B16'
              "
            />
          </div>
          <p
            class="vdb-c-flex-grow vdb-c-text-left vdb-c-text-xs vdb-c-font-medium md:vdb-c-text-sm md:vdb-c-font-semibold lg:vdb-c-text-base"
            :class="[
              {
                'vdb-c-text-pam': query.type === 'muted',
                'vdb-c-text-kilvish-900': query.type === 'primary',
                'vdb-c-text-orange-50': query.type === 'cta',
              },
            ]"
          >
            <component v-if="query.component" :is="query.component"></component>
            <span v-else class="vdb-c-break-words"> {{ query.content }} </span>
          </p>
        </div>
      </div>
    </div>

    <!-- Demo/Preview Videos -->
    <div
      class="vdb-c-flex vdb-c-w-full vdb-c-flex-col vdb-c-gap-12"
      v-if="enableVideoView"
    >
      <!-- Divider -->
      <div class="vdb-c-mt-12 vdb-c-h-1 vdb-c-w-full vdb-c-bg-[#EFEFEF]"></div>

      <!-- Headers -->
      <div
        class="vdb-c-text-base vdb-c-font-normal vdb-c-text-vdb-darkishgrey md:vdb-c-text-xl"
      >
        <!-- Demo Videos Header -->
        <div v-if="showDemoVideos">
          <div
            class="vdb-c-mb-12 vdb-c-flex vdb-c-items-center vdb-c-justify-between vdb-c-gap-4 md:vdb-c-mb-16"
          >
            <span
              class="vdb-c-w-1/2 vdb-c-text-lg vdb-c-font-semibold md:vdb-c-text-xl"
            >
              See agents in action:
            </span>

            <div class="vdb-c-flex vdb-c-items-center vdb-c-gap-16">
              <Button variant="secondary">
                <div
                  class="vdb-c-flex vdb-c-items-center vdb-c-justify-between vdb-c-gap-6"
                  @click="
                    $emit(
                      'view-all-videos-click',
                      'https://www.youtube.com/playlist?list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw',
                    )
                  "
                >
                  <div class="vdb-c-text-sm vdb-c-font-medium">
                    <span class="vdb-c-hidden md:vdb-c-block">
                      Watch more demos</span
                    >
                    <span class="vdb-c-block vdb-c-text-xs md:vdb-c-hidden">
                      More Demos
                    </span>
                  </div>
                  <ExternalLinkIcon class="vdb-c-hidden md:vdb-c-inline" />
                </div>
              </Button>
            </div>
          </div>
        </div>

        <!-- Preview Videos Header -->
        <div v-else>
          <div
            v-if="collectionName"
            class="vdb-c-flex vdb-c-items-center vdb-c-justify-between vdb-c-gap-4"
          >
            <span class="vdb-c-w-4/6 vdb-c-text-lg md:vdb-c-text-xl">
              {{ collectionName }}
            </span>
            <div class="vdb-c-flex vdb-c-items-center vdb-c-gap-16">
              <Button
                variant="secondary"
                @click="$emit('view-all-videos-click')"
                class="!vdb-c-px-8 !vdb-c-py-10"
              >
                <div
                  class="vdb-c-flex vdb-c-items-center vdb-c-justify-between vdb-c-gap-6"
                >
                  <div class="vdb-c-text-xs vdb-c-font-medium md:vdb-c-text-sm">
                    View all
                  </div>
                  <ChevronRightCircled class="vdb-c-hidden md:vdb-c-block" />
                </div>
              </Button>
            </div>
          </div>
          <div v-else>
            <div
              class="vdb-c-inline-block vdb-c-h-[3rem] vdb-c-w-full vdb-c-animate-pulse vdb-c-rounded vdb-c-bg-roy"
            ></div>
          </div>
        </div>
      </div>

      <!-- Videos -->
      <div
        v-if="!isContentLoading"
        class="vdb-c-grid vdb-c-grid-cols-12 vdb-c-gap-12 sm:vdb-c-gap-18"
      >
        <div
          v-for="(item, index) in previewMedia"
          :key="`post-${item.id}`"
          class="vdb-c-col-span-12 sm:vdb-c-col-span-6 md:vdb-c-col-span-4 lg:vdb-c-col-span-3"
        >
          <video-card
            v-if="item.type !== 'audio' && item.type !== 'image'"
            :item="item"
            :index="index"
            :variant="showDemoVideos ? 'hide-title' : 'default'"
            @video-click="$emit('video-click', $event)"
            @delete-video="$emit('delete-video', $event)"
          />

          <AudioCard
            v-else-if="item.type === 'audio'"
            :item="item"
            :index="index"
            :get-audio-url="getAudioUrl"
            @delete-audio="$emit('delete-audio', $event)"
          />

          <ImageCard
            v-else-if="item.type === 'image'"
            :item="item"
            :index="index"
            :get-image-url="getImageUrl"
            @delete-image="$emit('delete-image', $event)"
          />
        </div>
      </div>

      <!-- Videos Loader -->
      <div
        v-else
        class="vdb-c-grid vdb-c-w-full vdb-c-grid-cols-12 vdb-c-gap-24"
      >
        <div
          v-for="(item, index) in [1, 2, 3, 4]"
          :key="`post-loading-${index}`"
          class="vdb-c-col-span-12 sm:vdb-c-col-span-6 md:vdb-c-col-span-4 lg:vdb-c-col-span-3"
        >
          <video-card-loader :index="index" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

import VideoCard from "../../collection/VideoCard.vue";
import AudioCard from "../../collection/AudioCard.vue";
import ImageCard from "../../collection/ImageCard.vue";
import VideoCardLoader from "../../collection/VideoCardLoader.vue";

import Button from "../../buttons/Button.vue";

import ChevronRightCircled from "../../icons/ChevronRightCircled.vue";
import ExternalLinkIcon from "../../icons/ExternalLink.vue";
import QuestionMark from "../../icons/QuestionMark.vue";
import StarIcon from "../../icons/Star.vue";

const props = defineProps({
  actionCardQueries: {
    type: Array,
    default: () => [],
  },
  enableVideoView: {
    type: Boolean,
    default: true,
  },
  showDemoVideos: {
    type: Boolean,
    default: true,
  },
  previewMedia: {
    type: Array,
    default: null,
  },
  collectionData: {
    type: Object,
    default: () => null,
  },
  getAudioUrl: {
    type: Function,
  },
  getImageUrl: {
    type: Function,
  },
  isContentLoading: {
    type: Boolean,
    default: true,
  },
});

console.log(props.isContentLoading, props.previewMedia);

const collectionName = computed(() => props.collectionData?.name);

defineEmits([
  "query-card-click",
  "video-click",
  "view-all-videos-click",
  "upload-button-click",
  "delete-video",
  "delete-audio",
  "delete-image",
]);
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.fade-in-anim {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.action-card-shadow {
  box-shadow: 0px 15px 29px 0px #0000004d;
}
</style>
