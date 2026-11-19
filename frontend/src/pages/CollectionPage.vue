<template>
  <div class="mx-auto w-full max-w-1120 px-16 py-24 md:px-24">
    <CollectionView
      :collection-id="collectionId"
      :collection-data="collections.activeCollection ?? undefined"
      :collection-videos="collections.videos ?? undefined"
      :collection-audios="collections.audios ?? undefined"
      :collection-images="collections.images ?? undefined"
      @video-click="openVideo"
      @delete="(m) => (ui.pendingDelete = { kind: m.type ?? 'video', media: m })"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute } from "vue-router";

import CollectionView from "@/components/chat/CollectionView.vue";
import { useOpenVideo } from "@/composables/useOpenVideo";
import { useChatStore } from "@/stores/chat";
import { useCollectionsStore } from "@/stores/collections";
import { useUiStore } from "@/stores/ui";

const route = useRoute();
const chat = useChatStore();
const collections = useCollectionsStore();
const ui = useUiStore();
const openVideo = useOpenVideo();

const collectionId = computed(() => route.params.collectionId as string);

chat.reset();
watch(collectionId, (id) => id && collections.setActive(id), {
  immediate: true,
});
</script>
