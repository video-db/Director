<template>
  <div class="flex w-full flex-col gap-12 text-left" :class="{ 'items-end': isUser }">
    <LoadingMessage v-if="!isUser" :status="content.status ?? 'progress'" :message="content.status_message" />

    <template v-if="(content.status === 'success' || isUser) && image.url">
      <img
        v-if="!failed"
        :src="image.url"
        :alt="image.name || image.description || (isUser ? 'Attached image' : 'Generated image')"
        class="h-auto max-h-400 w-full max-w-sm rounded-md border border-border-neutral-primary object-contain"
        @error="failed = true"
      />
      <div
        v-else
        class="flex aspect-video w-full max-w-sm items-center justify-center gap-8 rounded-md border border-border-neutral-primary bg-background-neutral-subtle text-sm text-text-neutral-tertiary"
      >
        <Icon name="broken_image" :size="20" />
        Couldn't load the image
      </div>
    </template>

    <Skeleton v-else-if="content.status === 'progress'" class="aspect-square w-full max-w-sm rounded-md" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import { Icon } from "@/components/ui/icon";
import { Skeleton } from "@/components/ui/skeleton";
import type { ContentBase, Image } from "@/types";

import LoadingMessage from "./elements/LoadingMessage.vue";

const props = defineProps<{
  content: ContentBase & { image?: Partial<Image> };
  isUser?: boolean;
  convId?: string;
  msgId?: string;
}>();

const image = computed(() => props.content.image ?? {});
const failed = ref(false);
</script>
