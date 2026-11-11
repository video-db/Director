<template>
  <div class="vdb-c-py-24">
    <div
      v-if="collectionName"
      class="vdb-c-flex vdb-c-items-center vdb-c-gap-20"
      :style="{ lineHeight: '1.2' }"
    >
      <button
        @click="$emit('toggle-sidebar')"
        class="vdb-c-flex vdb-c-flex-none lg:vdb-c-hidden"
      >
        <div
          class="vdb-c-flex vdb-c-h-24 vdb-c-w-24 vdb-c-flex-col vdb-c-items-center vdb-c-justify-center"
        >
          <div class="vdb-c-mb-2 vdb-c-h-2 vdb-c-w-20 vdb-c-bg-gray-900"></div>
          <div class="vdb-c-mb-2 vdb-c-h-2 vdb-c-w-20 vdb-c-bg-gray-900"></div>
          <div class="vdb-c-mb-2 vdb-c-h-2 vdb-c-w-20 vdb-c-bg-gray-900"></div>
        </div>
      </button>
      <div
        class="vdb-c-flex vdb-c-grow vdb-c-items-center vdb-c-justify-between vdb-c-overflow-hidden"
      >
        <div
          :class="[
            'vdb-c-flex vdb-c-grow vdb-c-overflow-hidden',
            {
              'vdb-c-text-lg vdb-c-font-bold vdb-c-text-orange sm:vdb-c-text-2xl md:vdb-c-text-4xl md:vdb-c-font-extrabold':
                headerState === 'primary',
              'vdb-c-text-lg vdb-c-font-bold vdb-c-text-black sm:vdb-c-text-xl md:vdb-c-text-xl md:vdb-c-font-semibold':
                headerState === 'secondary',
            },
          ]"
        >
          <button
            v-if="collectionName"
            :title="collectionName"
            @click="openCollection"
            class="vdb-c-truncate"
            :class="videoName ? 'vdb-c-max-w-[33%]' : 'vdb-c-max-w-[83%]'"
          >
            {{ collectionName }}
            <span v-if="videoName"> </span>
          </button>
          <span
            v-if="videoName"
            :title="videoName"
            class="vdb-c-max-w-[50%] vdb-c-truncate"
          >
            > <span class="vdb-c-font-normal"> {{ videoName }} </span>
          </span>
        </div>

        <!-- Upload Icon -->
        <Button
          v-if="headerConfig.uploadButton"
          @click="$emit('upload-button-click')"
          variant="tertiary"
          class="vdb-c-flex-none !vdb-c-px-8 !vdb-c-py-10"
        >
          <div
            class="vdb-c-flex vdb-c-items-center vdb-c-gap-6 vdb-c-text-sm vdb-c-font-medium"
          >
            <UploadIcon
              class="vdb-c-hidden vdb-c-h-20 vdb-c-w-20 md:vdb-c-block"
            />
            <span class="vdb-c-flex vdb-c-flex-row vdb-c-gap-4">
              Upload <span class="vdb-c-hidden md:vdb-c-inline"> Media </span>
            </span>
          </div>
        </Button>
      </div>
    </div>

    <!-- Skeleton loading -->
    <div
      v-else
      class="vdb-c-inline-block vdb-c-h-[2rem] vdb-c-w-4/6 vdb-c-animate-pulse vdb-c-rounded vdb-c-bg-roy md:vdb-c-h-[2.5rem]"
    ></div>
  </div>
</template>

<script setup>
import Button from "../../buttons/Button.vue";
import UploadIcon from "../../icons/FileUpload.vue";

const props = defineProps({
  collectionName: {
    type: String,
    default: null,
  },
  videoName: {
    type: String,
    default: null,
  },
  headerState: {
    type: String,
    default: "primary",
  },
  headerConfig: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits([
  "collection-click",
  "upload-button-click",
  "toggle-sidebar",
]);

const openCollection = () => {
  const collectionName = props.collectionName;
  emit("collection-click", collectionName);
};
</script>

<style scoped></style>
