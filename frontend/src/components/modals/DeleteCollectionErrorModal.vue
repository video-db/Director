<template>
  <div
    v-if="isVisible"
    class="vdb-c-fixed vdb-c-inset-0 vdb-c-z-50 vdb-c-flex vdb-c-items-center vdb-c-justify-center vdb-c-bg-black vdb-c-bg-opacity-50"
    @click="closeModal"
  >
    <div
      class="vdb-c-shadow-xl vdb-c-m-10 vdb-c-w-[500px] vdb-c-overflow-hidden vdb-c-rounded-lg vdb-c-bg-white vdb-c-px-24 vdb-c-py-16"
      @click.stop
    >
      <!-- Header with icon and title -->
      <div class="vdb-c-mb-12 vdb-c-flex vdb-c-items-center vdb-c-gap-16">
        <div
          class="vdb-c-flex vdb-c-h-40 vdb-c-w-40 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-bg-red-100"
        >
          <WarningExclamation
            class="vdb-c-h-24 vdb-c-w-24 vdb-c-text-red-600"
          />
        </div>
        <h2 class="vdb-c-text-lg vdb-c-font-medium vdb-c-text-gray-950">
          Unable to delete this collection
        </h2>
      </div>

      <!-- Content -->
      <p
        class="vdb-c-mb-16 vdb-c-ml-[55px] vdb-c-text-sm vdb-c-font-normal vdb-c-text-[#6B7280]"
      >
        <slot name="description">
          This collection contains media. If you wish to delete this collection,
          kindly remove all the media individually first.
        </slot>
      </p>

      <!-- Footer -->
      <div class="vdb-c-flex vdb-c-justify-end">
        <button
          @click="closeModal"
          class="vdb-c-shadow-sm vdb-c-rounded-md vdb-c-bg-black vdb-c-px-16 vdb-c-py-8 vdb-c-text-sm vdb-c-font-medium vdb-c-text-white hover:vdb-c-bg-gray-800"
        >
          Okay
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import WarningExclamation from "../icons/WarningExclamation.vue";

defineProps({
  isVisible: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["closeModal"]);

const closeModal = () => {
  emit("closeModal");
};
</script>

<style scoped></style>
