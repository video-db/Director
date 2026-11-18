<template>
  <header
    class="flex h-56 shrink-0 items-center gap-8 border-b border-border-neutral-primary bg-background-neutral-primary px-16"
  >
    <SidebarTrigger />
    <Breadcrumb v-if="steps.length" :steps="steps" :link-as="RouterLink" class="min-w-0 flex-1" />
    <div v-else class="flex-1" />
    <Button
      hierarchy="secondary"
      size="sm"
      icon="upload"
      :disabled="!ready"
      @click="ui.showUploadDialog = true"
    >
      Upload
    </Button>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { Breadcrumb, type BreadcrumbStep } from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useCollectionsStore } from "@/stores/collections";
import { useUiStore } from "@/stores/ui";

defineProps<{ ready: boolean }>();

const route = useRoute();
const router = useRouter();
const collections = useCollectionsStore();
const ui = useUiStore();

// Collection › Video, wherever a collection or video is in focus.
const steps = computed<BreadcrumbStep[]>(() => {
  const collection = collections.activeCollection;
  if (!collection || route.name === "home" || route.name === "setup") return [];
  const out: BreadcrumbStep[] = [
    {
      label: collection.name,
      icon: "folder",
      href: router.resolve({ name: "collection", params: { collectionId: collection.id } }).href,
    },
  ];
  const video = collections.activeVideo;
  if (video && (route.name === "video" || route.name === "chat")) {
    out.push({ label: video.name });
  }
  return out;
});
</script>
