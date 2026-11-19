<template>
  <div class="flex flex-col gap-24">
    <SectionHeader
      :title="collectionData?.name ?? 'Collection'"
      :description="collectionData?.description || undefined"
      :count="loaded ? allAssets.length : undefined"
    >
    </SectionHeader>

    <div v-if="loaded && allAssets.length" class="flex flex-col gap-12 sm:flex-row sm:items-center sm:justify-between">
      <!-- Up to 5 name suggestions while typing, as before. -->
      <div class="relative w-full sm:max-w-320" @focusin="suggestOpen = true" @focusout="onSearchBlur">
        <SearchInput v-model="searchQuery" size="sm" placeholder="Search by name" class="w-full" />
        <ul
          v-if="suggestOpen && suggestions.length"
          class="absolute top-full z-20 mt-4 w-full rounded-sm border border-border-neutral-primary bg-background-neutral-primary p-4 shadow-md"
        >
          <li v-for="item in suggestions" :key="item.id">
            <button
              type="button"
              class="flex w-full items-center gap-8 rounded-xs px-8 py-6 text-left text-sm text-text-neutral-secondary hover:bg-background-neutral-hover"
              @mousedown.prevent="pick(item.name)"
            >
              <Icon name="search" :size="16" class="shrink-0 text-icon-neutral-tertiary" />
              <span class="truncate">
                <span v-for="(part, i) in highlight(item.name)" :key="i" :class="{ 'font-semibold text-text-neutral-primary': part.bold }">{{ part.text }}</span>
              </span>
            </button>
          </li>
        </ul>
      </div>
      <SegmentedControl v-model="mediaType" :options="mediaTypes" size="sm" label="Media type" />
    </div>

    <VideoListLoader v-if="!loaded" />
    <EmptyState
      v-else-if="!allAssets.length"
      icon="video_library"
      title="This collection is empty"
      description="Upload a video, audio file or image to start asking Director about it."
    >
      <Button hierarchy="primary" icon="upload" @click="ui.showUploadDialog = true">Upload media</Button>
    </EmptyState>
    <EmptyState
      v-else-if="!filteredAssets.length"
      icon="search_off"
      title="No matches"
      description="Try another name or media type."
    >
      <Button hierarchy="secondary" @click="clearFilters">Clear filters</Button>
    </EmptyState>
    <VideoList
      v-else
      :asset-results="filteredAssets"
      :items-per-page="12"
      @video-click="emit('video-click', $event)"
      @delete="emit('delete', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import VideoList from "@/components/collection/VideoList.vue";
import VideoListLoader from "@/components/collection/VideoListLoader.vue";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { SearchInput } from "@/components/ui/input";
import { SectionHeader } from "@/components/ui/section-header";
import { SegmentedControl, type SegmentedControlOption } from "@/components/ui/segmented-control";
import { useUiStore } from "@/stores/ui";
import type { Audio, Collection, Image, Media, Video } from "@/types";

const props = defineProps<{
  collectionId: string;
  collectionData?: Collection;
  collectionVideos?: Video[];
  collectionAudios?: Audio[];
  collectionImages?: Image[];
}>();

const emit = defineEmits<{ "video-click": [Video]; delete: [Media] }>();

const ui = useUiStore();

const mediaTypes: SegmentedControlOption[] = [
  { value: "all", label: "All" },
  { value: "video", label: "Video" },
  { value: "audio", label: "Audio" },
  { value: "image", label: "Image" },
];

const searchQuery = ref("");
const mediaType = ref("all");

const loaded = computed(
  () => !!props.collectionVideos && !!props.collectionAudios && !!props.collectionImages,
);

const allAssets = computed<Media[]>(() => [
  ...(props.collectionVideos ?? []),
  ...(props.collectionAudios ?? []),
  ...(props.collectionImages ?? []),
]);

const filteredAssets = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  return allAssets.value.filter(
    (asset) =>
      (mediaType.value === "all" || (asset.type ?? "video") === mediaType.value) &&
      (!query || asset.name?.toLowerCase().includes(query)),
  );
});

const suggestOpen = ref(false);
const suggestions = computed(() =>
  searchQuery.value.trim() ? filteredAssets.value.filter((a) => a.name !== searchQuery.value).slice(0, 5) : [],
);
function onSearchBlur(e: FocusEvent) {
  if (!(e.currentTarget as HTMLElement).contains(e.relatedTarget as Node)) suggestOpen.value = false;
}
function pick(name: string) {
  searchQuery.value = name;
  suggestOpen.value = false;
}
// The typed text stays regular; the rest of the name is bold.
function highlight(text: string) {
  const q = searchQuery.value.trim().toLowerCase();
  const i = text.toLowerCase().indexOf(q);
  if (!q || i === -1) return [{ text, bold: false }];
  return [
    { text: text.slice(0, i), bold: true },
    { text: text.slice(i, i + q.length), bold: false },
    { text: text.slice(i + q.length), bold: true },
  ].filter((p) => p.text);
}

function clearFilters() {
  searchQuery.value = "";
  mediaType.value = "all";
}
</script>
