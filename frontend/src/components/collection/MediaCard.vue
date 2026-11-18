<template>
  <!-- Collection videos play inline, as they always have. -->
  <VideoCard
    v-if="kind === 'video' && !demo && (item as Video).stream_url"
    :video="item as Video"
    deletable
    @delete="emit('delete', $event)"
  />
  <MediaThumbnail
    v-else
    :title="title"
    :type="kind"
    :src="src"
    :duration="kind === 'image' ? undefined : (item as Video | Audio).length"
    @select="onSelect"
  >
    <template v-if="kind === 'audio' && playing" #footer>
      <Badge colour="brand" size="sm" icon="graphic_eq">Playing</Badge>
    </template>
    <template v-if="!demo" #menu>
      <DropdownMenuItem icon="content_copy" @select="copyId">Copy ID</DropdownMenuItem>
      <DropdownMenuItem v-if="kind !== 'video' && url" icon="open_in_new" @select="openUrl">
        Open file
      </DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem icon="delete" tone="destructive" @select="emit('delete', item as Media)">
        Delete
      </DropdownMenuItem>
    </template>
  </MediaThumbnail>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import { Badge } from "@/components/ui/badge";
import VideoCard from "@/components/collection/VideoCard.vue";
import { DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { MediaThumbnail } from "@/components/ui/media-thumbnail";
import { useToast } from "@/components/ui/toast";
import { useCollectionsStore } from "@/stores/collections";
import type { Audio, Image, Media, Video } from "@/types";

// One video, audio or image in a grid. Demo videos (no collection) open on YouTube.
const props = defineProps<{ item: Media | (Partial<Video> & { id: string; external_url: string }) }>();
const emit = defineEmits<{ open: [Video]; delete: [Media] }>();

const collections = useCollectionsStore();
const { toast } = useToast();

const demo = computed(() => !("collection_id" in props.item) || !props.item.collection_id);
const kind = computed(() => (props.item.type ?? "video") as "video" | "audio" | "image");
const title = computed(() => (props.item as Media).name || "Demo video");
const url = ref<string>();
const src = computed(() =>
  kind.value === "video" ? (props.item as Video).thumbnail_url : kind.value === "image" ? url.value : undefined,
);

onMounted(async () => {
  if (demo.value || kind.value === "video") return;
  const item = props.item as Audio | Image;
  const get = kind.value === "image" ? collections.generateImageUrl : collections.generateAudioUrl;
  const res = await get(item.collection_id, item.id);
  if (res.status === "success") url.value = res.url as string;
});

// Audio plays in place; one card, one player.
const playing = ref(false);
let audio: HTMLAudioElement | null = null;
function toggleAudio() {
  if (!url.value) return;
  if (!audio) {
    audio = new window.Audio(url.value);
    audio.addEventListener("ended", () => (playing.value = false));
  }
  if (playing.value) audio.pause();
  else audio.play();
  playing.value = !playing.value;
}
onBeforeUnmount(() => audio?.pause());

function onSelect() {
  if (demo.value) {
    window.open((props.item as Video).external_url, "_blank", "noopener");
  } else if (kind.value === "video") {
    emit("open", props.item as Video);
  } else if (kind.value === "audio") {
    toggleAudio();
  } else {
    openUrl();
  }
}

function openUrl() {
  if (url.value) window.open(url.value, "_blank", "noopener");
}

async function copyId() {
  try {
    await navigator.clipboard.writeText(props.item.id);
    toast.success("Copied the ID");
  } catch {
    toast.error("Couldn't copy the ID");
  }
}
</script>
