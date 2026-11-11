<template>
  <button
    class="vdb-c-w-[80px] vdb-c-border-[1px] vdb-c-border-[#DADADA] vdb-c-px-4 vdb-c-py-6 vdb-c-text-center vdb-c-text-sm vdb-c-font-normal vdb-c-text-black"
    :class="{
      'vdb-c-text-orange vdb-c-bg-orange-50': state === 'active',
      'vdb-c-cursor-not-allowed': state === 'disabled',
      'vdb-c-border-l-0': !isFirst,
      'vdb-c-rounded-l-lg vdb-c-border-l': isFirst,
      'vdb-c-rounded-r-lg': isLast,
    }"
    @click="$emit('click', targetPage)"
    :disabled="state === 'disabled'"
  >
    {{ label }}
  </button>
</template>

<script setup>
const props = defineProps({
  label: {
    type: [String, Number],
    required: true,
  },
  targetPage: {
    type: Number,
    required: true,
  },
  state: {
    type: String,
    default: "default",
    validator: (value) => ["default", "active", "disabled"].includes(value),
  },
  isFirst: {
    type: Boolean,
    default: false,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["click"]);
</script>

<style></style>
