<template>
  <svg
    :class="className"
    width="28"
    height="28"
    viewBox="0 0 28 28"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M10.1751 2.97135C7.85552 1.34603 4.66663 3.00538 4.66663 5.83772V22.1626C4.66663 24.995 7.85555 26.6543 10.1751 25.029L21.8513 16.8473C23.8267 15.4631 23.8267 12.537 21.8513 11.1528L10.1751 2.97135Z"
      fill="white"
    />
  </svg>
</template>

<script>
export default {
  name: "Play",
  props: {
    className: {
      type: String,
      default: "",
    },
  },
};
</script>

<style scoped>
svg path {
  fill: currentColor;
}
</style>
