<template>
  <svg
    width="20"
    height="18"
    viewBox="0 0 20 18"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M10 7V9M10 13H10.01M3.07183 17H16.9282C18.4678 17 19.4301 15.3333 18.6603 14L11.7321 2C10.9623 0.666667 9.03778 0.666667 8.26798 2L1.33978 14C0.56998 15.3333 1.53223 17 3.07183 17Z"
      stroke="#DC2626"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script>
export default {
  props: {
    className: {
      type: String,
      default: "",
    },
  },
};
</script>

<style scoped>
/* svg path {
  fill: currentColor;
} */
</style>
