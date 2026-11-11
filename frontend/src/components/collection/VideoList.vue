<template>
  <div>
    <!-- Videos Grid -->
    <div class="vdb-c-grid vdb-c-grid-cols-12 vdb-c-gap-20">
      <div
        v-for="(item, index) in paginatedAssets"
        :key="`post-${item.id}`"
        class="vdb-c-col-span-12 sm:vdb-c-col-span-6"
        :class="[
          columns >= 4
            ? 'md:vdb-c-col-span-4 lg:vdb-c-col-span-3'
            : columns >= 3
              ? 'md:vdb-c-col-span-4 lg:vdb-c-col-span-4'
              : columns >= 2
                ? 'md:vdb-c-col-span-6 lg:vdb-c-col-span-6'
                : '',
        ]"
      >
        <video-card
          v-if="item.type !== 'audio' && item.type !== 'image'"
          :item="item"
          :index="index"
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

    <!-- Pagination -->
    <div
      v-if="showPagination"
      class="vdb-c-mt-20 vdb-c-flex vdb-c-justify-center"
    >
      <PaginationButton
        :target-page="-1"
        :state="currentPage === 1 ? 'disabled' : 'default'"
        :is-first="true"
        label="Previous"
        @click="goToPage"
      />

      <PaginationButton
        v-for="pageNumber in displayedPageNumbers"
        :key="pageNumber"
        :target-page="pageNumber"
        :state="currentPage === pageNumber ? 'active' : 'default'"
        :label="pageNumber"
        @click="goToPage"
      />

      <PaginationButton
        :target-page="totalPages + 1"
        :state="currentPage === totalPages ? 'disabled' : 'default'"
        :is-last="true"
        label="Next"
        @click="goToPage"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import AudioCard from "./AudioCard.vue";
import ImageCard from "./ImageCard.vue";
import PaginationButton from "./PaginationButton.vue";
import VideoCard from "./VideoCard.vue";

const props = defineProps({
  assetResults: {
    type: Array,
    default: () => [],
  },
  itemsPerPage: {
    type: Number,
    default: 8,
  },
  showPagination: {
    type: Boolean,
    default: true,
  },
  columns: {
    type: Number,
    default: 4,
    validator: (value) => value >= 1 && value <= 4,
  },
  getImageUrl: {
    type: Function,
  },
  getAudioUrl: {
    type: Function,
  },
});

const currentPage = ref(1);
const totalPages = computed(() =>
  Math.ceil(props.assetResults.length / props.itemsPerPage),
);

const paginatedAssets = computed(() => {
  if (!props.showPagination) {
    return props.assetResults;
  }
  const start = (currentPage.value - 1) * props.itemsPerPage;
  const end = start + props.itemsPerPage;
  return props.assetResults.slice(start, end);
});

const displayedPageNumbers = computed(() => {
  const maxDisplayed = 5;
  const halfDisplay = Math.floor(maxDisplayed / 2);

  let start = Math.max(1, currentPage.value - halfDisplay);
  let end = Math.min(totalPages.value, start + maxDisplayed - 1);

  // Adjust start if end is at its maximum
  if (end === totalPages.value) {
    start = Math.max(1, end - maxDisplayed + 1);
  }

  // Adjust end if start is at its minimum
  if (start === 1) {
    end = Math.min(totalPages.value, maxDisplayed);
  }

  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
});

const goToPage = (page) => {
  if (page < 1) {
    currentPage.value--;
  } else if (page > totalPages.value) {
    currentPage.value++;
  } else {
    currentPage.value = page;
  }
};

defineEmits(["video-click", "delete-video", "delete-audio", "delete-image"]);
</script>
