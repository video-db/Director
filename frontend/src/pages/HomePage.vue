<template>
  <div class="mx-auto flex w-full max-w-760 flex-col gap-40 px-16 py-40 md:px-24 md:py-64">
    <div class="flex flex-col gap-24">
      <div class="flex flex-col gap-8">
        <Logo brand="director" lockup="icon" :height="32" class="self-start" />
        <h1 class="text-h5 font-semibold text-text-neutral-primary">What are we working on today?</h1>
        <p class="text-md text-text-neutral-tertiary">
          Ask Director to find moments, cut clips, summarize or edit the videos in your collections.
        </p>
      </div>
      <div class="flex flex-col">
        <PromptSuggestion v-for="p in prompts" :key="p" @click="send({ text: p })">
          {{ p }}
        </PromptSuggestion>
      </div>
    </div>

    <section class="flex flex-col gap-16">
      <SectionHeader
        :title="showDemos ? 'See Director in action' : (collections.activeCollection?.name ?? 'Your media')"
        as="h2"
      >
        <template #action>
          <Button
            v-if="showDemos"
            as="a"
            hierarchy="tertiary"
            size="sm"
            icon="open_in_new"
            icon-position="trailing"
            href="https://www.youtube.com/playlist?list=PLhxAMFLSSK039xl1UgcZmoFLnb-qNRYQw"
            target="_blank"
            rel="noopener noreferrer"
          >
            More demos
          </Button>
          <Button
            v-else-if="collections.activeCollectionId"
            hierarchy="tertiary"
            size="sm"
            icon="arrow_forward"
            icon-position="trailing"
            @click="goToCollection"
          >
            View all
          </Button>
        </template>
      </SectionHeader>

      <!-- Thumbnails carry their own 12px hover padding, so it doubles as the gutter. -->
      <div class="-mx-12 grid grid-cols-2 md:grid-cols-4">
        <template v-if="collections.isContentLoading">
          <div v-for="n in 4" :key="n" class="p-12"><Skeleton class="aspect-video w-full rounded-sm" /></div>
        </template>
        <MediaCard
          v-for="item in previewMedia"
          v-else
          :key="item.id"
          :item="item"
          @open="openVideo"
          @delete="(m) => (ui.pendingDelete = { kind: m.type ?? 'video', media: m })"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import MediaCard from "@/components/collection/MediaCard.vue";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";
import { PromptSuggestion } from "@/components/ui/prompt-suggestion";
import { SectionHeader } from "@/components/ui/section-header";
import { Skeleton } from "@/components/ui/skeleton";
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

const showDemos = computed(() => collections.isFreshUser || collections.isEmpty);

const previewMedia = computed(() =>
  showDemos.value
    ? demoVideos
    : [...(collections.videos ?? []), ...(collections.audios ?? []), ...(collections.images ?? [])].slice(0, 4),
);

const prompts = computed(() => [
  "Upload https://youtu.be/FgrO9ADPZSA and give me a bullet point summary",
  "What can you do with my videos?",
  !collections.isFreshUser && collections.videos?.length
    ? "Categorize all videos in this collection"
    : "How do I search for a moment inside my videos?",
]);

function goToCollection() {
  if (!collections.activeCollectionId) return;
  router.push({ name: "collection", params: { collectionId: collections.activeCollectionId } });
}
</script>
