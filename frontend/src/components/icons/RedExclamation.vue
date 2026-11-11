

<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
  >
    <path
      d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z"
      stroke="#E2462C"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M12 7.5V12.75"
      stroke="#E2462C"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M12 17.0625C12.5178 17.0625 12.9375 16.6428 12.9375 16.125C12.9375 15.6072 12.5178 15.1875 12 15.1875C11.4822 15.1875 11.0625 15.6072 11.0625 16.125C11.0625 16.6428 11.4822 17.0625 12 17.0625Z"
      fill="#E2462C"
    />
  </svg>
</template>

<script>
export default {
  props: {
    className: {
      type: String,
      default: '',
    },
  },
}
</script>

<style scoped>
/* svg path {
  fill: currentColor;
} */
</style>
