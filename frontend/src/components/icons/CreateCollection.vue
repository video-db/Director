<template>
  <svg
    width="40"
    height="40"
    viewBox="0 0 40 40"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect width="40" height="40" rx="20" fill="#FFE9D3" />
    <path
      d="M12 14C12 12.8954 12.8954 12 14 12H16C17.1046 12 18 12.8954 18 14V16C18 17.1046 17.1046 18 16 18H14C12.8954 18 12 17.1046 12 16V14Z"
      stroke="#EC5B16"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M22 14C22 12.8954 22.8954 12 24 12H26C27.1046 12 28 12.8954 28 14V16C28 17.1046 27.1046 18 26 18H24C22.8954 18 22 17.1046 22 16V14Z"
      stroke="#EC5B16"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M12 24C12 22.8954 12.8954 22 14 22H16C17.1046 22 18 22.8954 18 24V26C18 27.1046 17.1046 28 16 28H14C12.8954 28 12 27.1046 12 26V24Z"
      stroke="#EC5B16"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M22 24C22 22.8954 22.8954 22 24 22H26C27.1046 22 28 22.8954 28 24V26C28 27.1046 27.1046 28 26 28H24C22.8954 28 22 27.1046 22 26V24Z"
      stroke="#EC5B16"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup>
defineProps({
  fillColor: {
    type: String,
    default: "#FFE9D3",
  },
  customClass: {
    type: String,
    default: "",
  },
});
</script>
