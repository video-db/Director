<template>
  <div class="vdb-c-w-[90%] vdb-c-p-16">
    <DefaultScreen
      class="vdb-c-transition-opacity vdb-c-duration-300 vdb-c-ease-in-out"
      :collection-data="collections.activeCollection ?? undefined"
      :action-card-queries="actionCards"
      :show-demo-videos="showDemoVideos"
      :enable-video-view="true"
      :is-content-loading="collections.isContentLoading"
      :preview-media="previewMedia"
      :get-image-url="collections.generateImageUrl"
      :get-audio-url="collections.generateAudioUrl"
      @query-card-click="handleQueryCardClick"
      @video-click="openVideo"
      @delete-video="ui.pendingDelete = { kind: 'video', media: $event }"
      @delete-audio="ui.pendingDelete = { kind: 'audio', media: $event }"
      @delete-image="ui.pendingDelete = { kind: 'image', media: $event }"
      @upload-button-click="ui.showUploadDialog = true"
      @view-all-videos-click="handleViewAll"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import DefaultScreen from "@/components/chat/elements/DefaultScreen.vue";
import UploadVideoQueryCard from "@/components/chat/elements/UploadVideoQueryCard.vue";
import CollectionIcon from "@/components/icons/Collection.vue";
import QueryIcon from "@/components/icons/Query.vue";
import SearchIcon from "@/components/icons/SearchIcon.vue";
import { useChatActions } from "@/composables/useChatActions";
import { useOpenVideo } from "@/composables/useOpenVideo";
import { demoVideos } from "@/config";
import { useChatStore } from "@/stores/chat";
import { useCollectionsStore } from "@/stores/collections";
import { useUiStore } from "@/stores/ui";

const router = useRouter();
const chat = useChatStore();
const collections = useCollectionsStore();
const ui = useUiStore();
const { send } = useChatActions();
const openVideo = useOpenVideo();

chat.reset();

const showDemoVideos = computed(
  () => collections.isFreshUser || collections.isEmpty,
);

const previewMedia = computed(() =>
  showDemoVideos.value
    ? demoVideos
    : [
        ...(collections.videos ?? []),
        ...(collections.audios ?? []),
        ...(collections.images ?? []),
      ].slice(0, 4),
);

const uploadCard = {
  component: UploadVideoQueryCard,
  content:
    "Upload <a href='https://www.youtube.com/watch?v=FgrO9ADPZSA' target='_blank'>https://youtu.be/FgrO9ADPZSA</a> and generate a bullet point summary.",
  type: "primary",
  action: "chat",
  icon: QueryIcon,
};
const capabilitiesCard = {
  content: "What can you do with my videos?",
  type: "primary",
  action: "chat",
};

const actionCards = computed(() => [
  uploadCard,
  capabilitiesCard,
  !collections.isFreshUser && collections.videos?.length
    ? {
        content: "Categorize all videos in this collection",
        type: "primary",
        action: "chat",
        icon: CollectionIcon,
      }
    : {
        content: "How do I search for a moment inside my videos?",
        type: "primary",
        action: "chat",
        icon: SearchIcon,
      },
]);

function goToCollection() {
  if (!collections.activeCollectionId) return;
  router.push({
    name: "collection",
    params: { collectionId: collections.activeCollectionId },
  });
}

function handleQueryCardClick(query: { action: string; content: string }) {
  chat.chatInput = "";
  if (query.action === "show-collection") goToCollection();
  else if (query.action === "chat") send({ text: query.content });
}

function handleViewAll(redirectTo = "") {
  if (redirectTo.includes("youtube.com")) window.open(redirectTo, "_blank");
  else goToCollection();
}
</script>
