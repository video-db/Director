<template>
  <div class="flex w-full flex-col gap-12 text-left">
    <LoadingMessage :status="content.status ?? 'progress'" :message="content.status_message" />

    <SearchListItem
      v-if="content.status === 'success' && results.length"
      :search-results="results"
      :is-contractable="results.length > 1"
    />

    <Card v-else-if="content.status === 'progress'" variant="outline" size="sm">
      <CardContent class="flex flex-col gap-16 sm:flex-row">
        <div class="flex flex-col gap-8 sm:w-2/5 sm:shrink-0">
          <Skeleton class="aspect-video w-full rounded-sm" />
          <Skeleton class="h-14 w-3/4" />
          <Skeleton class="h-12 w-1/3" />
        </div>
        <div class="flex flex-1 flex-col gap-12">
          <Skeleton v-for="i in 4" :key="i" class="h-14 w-full" />
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ContentBase } from "@/types";

import LoadingMessage from "./elements/LoadingMessage.vue";
import SearchListItem, { type SearchResult } from "./search/SearchListItem.vue";

const props = defineProps<{
  content: ContentBase & { search_results?: SearchResult[] };
  isLastConv?: boolean;
}>();

const results = computed(() => props.content.search_results ?? []);
</script>
