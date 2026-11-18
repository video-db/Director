<template>
  <div class="flex w-full flex-col gap-12">
    <Card
      v-for="(result, index) of visibleResults"
      :key="result.video_id ?? index"
      variant="outline"
      size="sm"
    >
      <CardContent class="@container">
        <div class="flex flex-col gap-16 @xl:flex-row">
          <div class="flex flex-col gap-8 @xl:w-2/5 @xl:shrink-0">
            <div class="overflow-hidden rounded-sm border border-border-neutral-primary">
              <VideoDBPlayer
                :ref="(el: unknown) => setPlayer(index, el)"
                :stream-url="result.stream_url"
                :default-controls="false"
                :default-overlay="false"
                @loadeddata="onLoaded(index)"
              >
                <template #overlay>
                  <BigCenterButton class="absolute top-1/2 left-1/2 size-48" />
                </template>
              </VideoDBPlayer>
            </div>
            <div class="flex flex-col gap-2">
              <p class="line-clamp-2 text-sm font-medium text-text-neutral-primary">
                {{ result.video_title || "Untitled video" }}
              </p>
              <p class="text-xs text-text-neutral-tertiary">
                {{ result.shots.length }} {{ result.shots.length === 1 ? "match" : "matches" }}
                <template v-if="result.duration"> · {{ formatDuration(result.duration) }}</template>
              </p>
            </div>
          </div>

          <!-- The player's own moments widget; clicking a moment seeks this result's player. -->
          <div class="min-w-0 flex-1 overflow-hidden rounded-sm border border-border-neutral-primary">
            <SearchResults
              :is-light="true"
              :search-results="formatHits(result)"
              :duration="durations[index] ?? result.duration ?? 0"
              :on-slide-click="(seconds: number) => playFrom(index, seconds)"
            />
          </div>
        </div>
      </CardContent>
    </Card>

    <Button
      v-if="isContractable"
      hierarchy="secondary"
      size="sm"
      class="self-center"
      :icon="isExpanded ? 'expand_less' : 'expand_more'"
      icon-position="trailing"
      @click="isExpanded = !isExpanded"
    >
      {{ isExpanded ? "See less" : "See more results" }}
    </Button>
  </div>
</template>

<script lang="ts">
// One video's hits, as the backend sends them (SearchData in core/session.py).
export interface SearchResult {
  video_id: string;
  video_title?: string;
  stream_url: string;
  duration?: number;
  shots: { start: number; end: number; text: string; search_score?: number }[];
}
</script>

<script setup lang="ts">

import { BigCenterButton, SearchResults, VideoDBPlayer } from "@videodb/player-vue";
import { computed, ref } from "vue";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatDuration } from "@/components/ui/duration-label";

// The parts of the player instance used here.
interface PlayerHandle {
  seekTo: (seconds: number) => void;
  togglePlay: () => void;
  playing: boolean;
  duration?: number;
}

const props = withDefaults(
  defineProps<{
    searchResults?: SearchResult[];
    isContractable?: boolean;
  }>(),
  { searchResults: () => [], isContractable: false },
);

const isExpanded = ref(!props.isContractable);
const visibleResults = computed(() =>
  isExpanded.value ? props.searchResults : props.searchResults.slice(0, 1),
);

const players: Record<number, PlayerHandle> = {};
function setPlayer(index: number, el: unknown) {
  if (el) players[index] = el as PlayerHandle;
}

const durations = ref<Record<number, number>>({});
function onLoaded(index: number) {
  const d = players[index]?.duration;
  if (d) durations.value[index] = d;
}

const formatHits = (result: SearchResult) => ({
  hits: result.shots.map((shot, i) => ({ id: `sr-${i}`, start: shot.start, end: shot.end, text: shot.text, type: "relevant" })),
});

function playFrom(index: number, seconds: number) {
  const player = players[index];
  if (!player) return;
  player.seekTo(seconds);
  if (!player.playing) player.togglePlay();
}
</script>
