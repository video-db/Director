<template>
  <div class="vdb-c-w-full vdb-c-py-16">
    <CollectionView
      :collection-id="collectionId"
      :collection-data="collections.activeCollection ?? undefined"
      :collection-videos="collections.videos ?? undefined"
      :collection-audios="collections.audios ?? undefined"
      :collection-images="collections.images ?? undefined"
      :get-image-url="collections.generateImageUrl"
      :get-audio-url="collections.generateAudioUrl"
      class="vdb-c-w-full vdb-c-transition-opacity vdb-c-duration-300 vdb-c-ease-in-out"
      @video-click="openVideo"
      @delete-video="ui.pendingDelete = { kind: 'video', media: $event }"
      @delete-audio="ui.pendingDelete = { kind: 'audio', media: $event }"
      @delete-image="ui.pendingDelete = { kind: 'image', media: $event }"
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
