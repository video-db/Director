<template>
  <div class="vdb-c-flex vdb-c-items-center vdb-c-justify-between">
    <div
      class="vdb-c-relative vdb-c-flex vdb-c-w-full vdb-c-justify-between vdb-c-pl-2 vdb-c-text-sm"
    >
      <div
        ref="inputContainer"
        :class="[
          'vdb-c-flex vdb-c-w-[90%] vdb-c-max-w-[400px] vdb-c-items-center vdb-c-rounded-[10px] vdb-c-border vdb-c-bg-gray-50 vdb-c-p-10 vdb-c-pr-8 vdb-c-text-sm vdb-c-text-black md:vdb-c-w-[60%]',
          isFocused
            ? 'vdb-c-border-[#EC5B16] vdb-c-shadow-[0_0_0_2px_rgba(236,91,22,0.25)]'
            : 'vdb-c-border-gray-300',
        ]"
      >
        <SearchIcon class="vdb-c-text-gray-700" />
        <input
          v-model="searchQuery"
          @input="handleInput"
          @focus="isFocused = true"
          @blur="isFocused = false"
          class="p-4 h-full vdb-c-block vdb-c-w-[100%] vdb-c-bg-gray-50 vdb-c-px-8 vdb-c-text-sm vdb-c-text-black vdb-c-placeholder-gray-700 vdb-c-outline-none"
          type="text"
          placeholder="Search"
        />
        <button
          class="vdb-c-flex vdb-c-size-[20px] vdb-c-items-center vdb-c-justify-center vdb-c-opacity-20 hover:vdb-c-opacity-100"
          v-if="searchQuery"
          @click="clearSearch"
        >
          <div
            class="vdb-c-flex vdb-c-size-[20px] vdb-c-items-center vdb-c-justify-center"
          >
            <SearchCrossIcon class="vdb-c-size-20" />
          </div>
        </button>
      </div>
      <ul
        ref="autocompleteContainer"
        v-if="showAutocomplete"
        class="autocomplete-drop-shadow vdb-c-absolute vdb-c-top-full vdb-c-z-10 vdb-c-mt-8 vdb-c-max-h-[60vh] vdb-c-w-[90%] vdb-c-max-w-[400px] vdb-c-cursor-pointer vdb-c-overflow-hidden vdb-c-overflow-y-scroll vdb-c-rounded-12 vdb-c-border vdb-c-border-roy vdb-c-bg-white vdb-c-p-8 vdb-c-text-sm md:vdb-c-w-[60%]"
      >
        <li
          class="vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-gap-10 vdb-c-overflow-x-hidden vdb-c-rounded-8 vdb-c-bg-white vdb-c-px-10 vdb-c-py-8 vdb-c-text-sm vdb-c-text-black hover:vdb-c-bg-roy"
          v-for="item in filteredAssets.slice(0, 5)"
          :key="item.id"
          @click="selectItem(item)"
        >
          <SearchIcon class="vdb-c-size-[15px] vdb-c-text-black" />
          <div class="vdb-c-w-4/5 md:vdb-c-w-11/12">
            <span
              v-for="(part, idx) in getHighlightedParts(item.name)"
              :key="idx"
            >
              <span class="vdb-c-font-semibold" v-if="part.bold">{{
                part.text
              }}</span>
              <span v-else>{{ part.text }}</span>
            </span>
          </div>
        </li>
      </ul>
    </div>
    <div ref="mediaTypeContainer" class="vdb-c-relative">
      <button
        @click="toggleMediaDropdown"
        class="vdb-c-flex vdb-c-min-w-[120px] vdb-c-items-center vdb-c-justify-between vdb-c-gap-10 vdb-c-rounded-8 vdb-c-border vdb-c-border-roy vdb-c-bg-white vdb-c-px-[11px] vdb-c-py-10 vdb-c-text-[15px] vdb-c-font-semibold vdb-c-text-black vdb-c-shadow-[0px_1px_1px_rgba(0,0,0,0.05)]"
      >
        <p class="vdb-c-w-full vdb-c-text-[#1F2937]">
          {{ currentMediaType.name }}
        </p>
        <ChevronDown :class="{ 'vdb-c-rotate-180': showMediaDropdown }" />
      </button>
      <ul
        v-if="showMediaDropdown"
        class="multi-dropdown-shadow vdb-c-absolute vdb-c-right-0 vdb-c-top-[calc(100%+8px)] vdb-c-z-10 vdb-c-w-[190%] vdb-c-cursor-pointer vdb-c-rounded-12 vdb-c-border vdb-c-border-roy vdb-c-bg-white vdb-c-p-8 vdb-c-text-sm"
      >
        <li
          class="vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-justify-between vdb-c-gap-12 vdb-c-rounded-8 vdb-c-bg-white vdb-c-px-12 vdb-c-py-8 vdb-c-text-sm vdb-c-font-[500] vdb-c-text-black hover:vdb-c-bg-roy"
          v-for="item in mediaTypes"
          :key="item.id"
          @click="selectMedia(item)"
        >
          <div>
            {{ item.name === "All files" ? "All" : item.name }}
          </div>
          <RedCheck v-if="item.id === currentMediaType.id" />
        </li>
      </ul>
    </div>
  </div>
  <div class="vdb-c-mx-auto vdb-c-w-11/12 vdb-c-pb-4 vdb-c-pt-28">
    <div v-if="collectionVideos !== null">
      <VideoList
        v-if="videos.length > 0"
        :asset-results="filteredAssets"
        :get-image-url="getImageUrl"
        :get-audio-url="getAudioUrl"
        @video-click="handleVideoClick"
        @delete-video="emit('delete-video', $event)"
        @delete-image="emit('delete-image', $event)"
        @delete-audio="emit('delete-audio', $event)"
      />
      <div
        v-else
        class="vdb-c-flex vdb-c-flex-col vdb-c-items-center vdb-c-justify-center vdb-c-gap-32 vdb-c-py-32 vdb-c-text-center vdb-c-text-black"
      >
        <div class="vdb-c-text-2xl vdb-c-font-bold">
          Your Collection is empty
        </div>
        <Button
          @click="send({ text: 'Upload a video to this collection' })"
          variant="tertiary"
          class="vdb-c-mt-12"
        >
          <div class="vdb-c-flex vdb-c-items-center vdb-c-gap-6">
            <UploadIcon />
            <span>Upload a video</span>
          </div>
        </Button>
      </div>
    </div>

    <VideoListLoader v-else />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useChatActions } from "@/composables/useChatActions";
import Button from "../buttons/Button.vue";
import VideoList from "../collection/VideoList.vue";
import VideoListLoader from "../collection/VideoListLoader.vue";
import ChevronDown from "../icons/ChevronDown.vue";
import UploadIcon from "../icons/FileUpload.vue";
import RedCheck from "../icons/RedCheck.vue";
import SearchCrossIcon from "../icons/SearchCross.vue";
import SearchIcon from "../icons/SearchIcon.vue";

const { send } = useChatActions();

const props = defineProps({
  collectionId: {
    type: String,
    required: true,
  },
  collectionData: {
    type: Object,
    default: null,
  },
  collectionVideos: {
    type: Array,
    default: null,
  },
  collectionAudios: {
    type: Array,
    default: null,
  },
  collectionImages: {
    type: Array,
    default: null,
  },
  getAudioUrl: {
    type: Function,
  },
  getImageUrl: {
    type: Function,
  },
});

const mediaTypes = [
  {
    id: "all_files",
    name: "All files",
  },
  {
    id: "videos",
    name: "Video",
  },
  {
    id: "audios",
    name: "Audio",
  },
  {
    id: "images",
    name: "Image",
  },
];

const hover = ref(false);
const isFocused = ref(false);
const searchQuery = ref("");
const showAutocomplete = ref(false);
const showMediaDropdown = ref(false);
const currentMediaType = ref(mediaTypes[0]);

const inputContainer = ref(null);
const autocompleteContainer = ref(null);
const mediaTypeContainer = ref(null);

const handleClickOutside = (event) => {
  if (
    autocompleteContainer.value &&
    !autocompleteContainer.value.contains(event.target)
  ) {
    showAutocomplete.value = false;
  }

  if (inputContainer.value && !inputContainer.value.contains(event.target)) {
    showAutocomplete.value = false;
  }

  if (
    mediaTypeContainer.value &&
    !mediaTypeContainer.value.contains(event.target)
  ) {
    showMediaDropdown.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleClickOutside);
});

const clearSearch = () => {
  searchQuery.value = "";
};

function toggleMediaDropdown() {
  showMediaDropdown.value = !showMediaDropdown.value;
}

function selectMedia(item) {
  currentMediaType.value = item;
  showMediaDropdown.value = false;
}

const handleInput = () => {
  showAutocomplete.value = searchQuery.value.trim() !== "";
};

const selectItem = (item) => {
  searchQuery.value = item.name;
  showAutocomplete.value = false;
};

const emit = defineEmits([
  "video-click",
  "delete-video",
  "delete-audio",
  "delete-image",
  "get-image-url",
  "get-audio-url",
]);

const videos = computed(() => {
  if (props.collectionVideos === null) {
    return [];
  }
  return props.collectionVideos;
});

const audios = computed(() => {
  if (props.collectionAudios === null) {
    return [];
  }
  return props.collectionAudios;
});

const images = computed(() => {
  if (props.collectionImages === null) {
    return [];
  }
  return props.collectionImages;
});

const filteredAssets = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();
  let assets = [];
  if (currentMediaType.value.id === "all_files") {
    assets = [...videos.value, ...audios.value, ...images.value];
  } else if (currentMediaType.value.id === "videos") {
    assets = [...videos.value];
  } else if (currentMediaType.value.id === "audios") {
    assets = [...audios.value];
  } else if (currentMediaType.value.id === "images") {
    assets = [...images.value];
  }
  if (!query) return assets;
  return assets.filter((asset) => asset.name?.toLowerCase().includes(query));
});
const getHighlightedParts = (text) => {
  const query = searchQuery.value.trim();
  if (!query) return [{ text, bold: false }];

  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();

  let parts = [];

  let matchIndex = lowerText.indexOf(lowerQuery);
  if (matchIndex === -1) {
    return [{ text, bold: false }];
  }

  if (matchIndex > 0) {
    parts.push({ text: text.slice(0, matchIndex), bold: true });
  }

  parts.push({
    text: text.slice(matchIndex, matchIndex + query.length),
    bold: false,
  });

  if (matchIndex + query.length < text.length) {
    parts.push({ text: text.slice(matchIndex + query.length), bold: true });
  }

  return parts;
};

const handleVideoClick = (video) => {
  emit("video-click", video);
};
</script>
<style>
.autocomplete-drop-shadow {
  box-shadow:
    5px 5px 11px 0px rgba(0, 0, 0, 0.06),
    10px 21px 21px 0px rgba(0, 0, 0, 0.05),
    20px 47px 28px 0px rgba(0, 0, 0, 0.03),
    30px 83px 33px 0px rgba(0, 0, 0, 0.01),
    40px 130px 36px 0px rgba(0, 0, 0, 0);
}

.multi-dropdown-shadow {
  box-shadow:
    0px 5px 11px rgba(0, 0, 0, 0.06),
    0px 21px 21px rgba(0, 0, 0, 0.05),
    0px 47px 28px rgba(0, 0, 0, 0.03),
    0px 83px 33px rgba(0, 0, 0, 0.01),
    0px 130px 36px rgba(0, 0, 0, 0);
}
</style>
