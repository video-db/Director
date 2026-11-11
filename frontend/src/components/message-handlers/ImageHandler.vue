<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    class="vdb-c-relative vdb-c-flex vdb-c-w-full vdb-c-flex-col vdb-c-gap-8 vdb-c-bg-white vdb-c-py-14 vdb-c-text-left"
  >
    <LoadingMessage
      v-if="!isUser"
      :status="content.status"
      :message="content.status_message"
      :isLastConv="isLastConv"
    />

    <transition name="fade" mode="out-in">
      <div
        v-if="content.status === 'success' || isUser"
        class="vdb-c-shadow-md vdb-c-overflow-hidden"
      >
        <img
          :src="image.url"
          :alt="'Generated image'"
          class="vdb-c-max-h-[50vh] vdb-c-h-auto vdb-c-w-4/5 vdb-c-max-w-[400px] vdb-c-rounded-lg sm:vdb-c-w-3/4 md:vdb-c-w-1/2"
        />
      </div>
      <div
        v-else-if="content.status === 'progress'"
        class="vdb-c-animate-pulse vdb-c-rounded-lg vdb-c-bg-gray-200"
      ></div>
      <div
        v-else-if="content.status === 'error'"
        class="vdb-c-flex vdb-c-flex-col"
      >
        <p class="vdb-c-text-red-500">Error loading image.</p>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed } from "vue";
import LoadingMessage from "./elements/LoadingMessage.vue";

const props = defineProps({
  content: {
    type: Object,
    required: true,
  },
  isUser: {
    type: Boolean,
    default: false,
  },
  isLastConv: {
    type: Boolean,
    default: false,
  },
});

const image = computed(() => props.content.image || {});
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
