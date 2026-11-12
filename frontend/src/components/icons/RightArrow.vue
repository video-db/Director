<template>
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="className"
  >
    <path
      d="M5 12H19M19 12L12 5M19 12L12 19"
      :stroke="strokeColor"
      :stroke-width="strokeWidth"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup>
defineProps({
  className: {
    type: String,
    default: "",
  },
  strokeWidth: {
    type: Number,
    default: 1.5,
  },
  strokeColor: {
    type: String,
    default: "#20557D",
  },
});
</script>
