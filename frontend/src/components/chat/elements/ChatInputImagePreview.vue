<template>
  <div v-if="attachment" class="vdb-c-relative vdb-c-flex vdb-c-items-center">
    <div
      class="vdb-c-relative vdb-c-flex vdb-c-h-[60px] vdb-c-w-[60px] vdb-c-items-center vdb-c-justify-center vdb-c-overflow-hidden"
    >
      <img
        :src="getImageSrc"
        alt="Image Preview"
        class="vdb-c-absolute vdb-c-bottom-0 vdb-c-left-0 vdb-c-h-[90%] vdb-c-w-[90%] vdb-c-rounded-8 vdb-c-object-cover"
        @load="handleImageLoad"
        @error="handleImageError"
      />

      <div
        v-if="loading"
        class="vdb-c-absolute vdb-c-bottom-0 vdb-c-left-0 vdb-c-flex vdb-c-h-[90%] vdb-c-w-[90%] vdb-c-items-center vdb-c-justify-center vdb-c-bg-white/80"
      >
        <div class="vdb-c-flex vdb-c-items-center vdb-c-justify-center">
          <div
            class="vdb-c-h-24 vdb-c-w-24 vdb-c-animate-spin vdb-c-rounded-full vdb-c-border-4 vdb-c-border-orange vdb-c-border-t-transparent"
          ></div>
        </div>
      </div>

      <button
        v-if="!loading"
        class="vdb-c-absolute vdb-c-right-0 vdb-c-top-0 vdb-c-flex vdb-c-h-[33%] vdb-c-w-[33%] vdb-c-cursor-pointer vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-border vdb-c-border-white vdb-c-bg-black vdb-c-transition-colors"
        @click="$emit('remove')"
      >
        <CrossIcon fill="white" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import CrossIcon from "../../icons/Cross.vue";

const props = defineProps({
  attachment: {
    type: Object,
    required: true,
  },
});

defineEmits(["remove"]);

const imageLoading = ref(true);

const getImageSrc = computed(() => {
  if (props.attachment.image_data instanceof File) {
    return URL.createObjectURL(props.attachment.image_data);
  } else if (props.attachment.image_data?.startsWith("data:")) {
    return props.attachment.image_data; // Base64 URL
  }
  return props.attachment.url; // Regular URL
});

const loading = computed(
  () =>
    imageLoading.value ||
    props.attachment?.upload_status === "uploading" ||
    props.attachment?.upload_status === "in_queue",
);

const handleImageLoad = () => {
  imageLoading.value = false;
};

const handleImageError = () => {
  imageLoading.value = false;
  // Could add error handling here
};
</script>
