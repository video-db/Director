<template>
  <div
    v-if="showDialog"
    class="vdb-c-fixed vdb-c-inset-0 vdb-c-z-50 vdb-c-flex vdb-c-items-center vdb-c-justify-center vdb-c-bg-black/50"
    @click="$emit('cancel-delete')"
  >
    <div
      class="vdb-c-shadow-xl vdb-c-m-10 vdb-c-overflow-hidden vdb-c-rounded-lg vdb-c-bg-white"
      @click.stop
    >
      <div class="vdb-c-flex vdb-c-gap-16 vdb-c-px-24 vdb-c-py-16 vdb-c-pt-24">
        <div
          class="vdb-c-flex vdb-c-h-40 vdb-c-w-40 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-bg-red-100"
        >
          <warning-exclamation />
        </div>
        <div class="vdb-c-flex vdb-c-flex-col vdb-c-gap-8">
          <h2 class="vdb-c-text-lg vdb-c-font-medium vdb-c-text-gray-950">
            {{ headingText }}
          </h2>
          <p class="vdb-c-text-sm vdb-c-font-normal vdb-c-text-[#6B7280]">
            {{ descriptionText }}
          </p>
        </div>
      </div>
      <div
        class="vdb-c-flex vdb-c-w-full vdb-c-justify-end vdb-c-gap-12 vdb-c-bg-gray-50 vdb-c-px-24 vdb-c-py-12"
      >
        <button
          @click="$emit('cancel-delete')"
          class="vdb-c-shadow-sm vdb-c-rounded-md vdb-c-border vdb-c-border-gray-300 vdb-c-bg-white vdb-c-px-16 vdb-c-py-8 vdb-c-text-sm vdb-c-font-medium vdb-c-text-gray-700 hover:vdb-c-bg-gray-300"
        >
          {{ cancelButtonText }}
        </button>
        <button
          @click="$emit('confirm-delete')"
          class="vdb-c-shadow-sm vdb-c-rounded-md vdb-c-bg-[#DC2626] vdb-c-px-16 vdb-c-py-8 vdb-c-text-sm vdb-c-font-medium vdb-c-text-white hover:vdb-c-bg-[#B91C1C]"
        >
          {{ actionButtonText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from "vue";
import WarningExclamation from "../icons/WarningExclamation.vue";
defineProps({
  showDialog: {
    type: Boolean,
    default: false,
  },
  headingText: {
    type: String,
    default: "Are you sure ?",
  },
  descriptionText: {
    type: String,
    default: "",
  },
  actionButtonText: {
    type: String,
    default: "Confirm",
  },
  cancelButtonText: {
    type: String,
    default: "Cancel",
  },
});
defineEmits(["cancel-delete", "confirm-delete"]);
</script>
