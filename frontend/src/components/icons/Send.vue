<template>
  <svg
    :class="className"
    xmlns="http://www.w3.org/2000/svg"
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="none"
  >
    <path
      d="M3.66667 16.1875C3.38889 16.2986 3.125 16.2743 2.875 16.1146C2.625 15.9549 2.5 15.7222 2.5 15.4167V11.6667L9.16667 10L2.5 8.33335V4.58335C2.5 4.27779 2.625 4.04516 2.875 3.88543C3.125 3.72571 3.38889 3.70141 3.66667 3.81252L16.5 9.22918C16.8472 9.38196 17.0208 9.63891 17.0208 10C17.0208 10.3611 16.8472 10.6181 16.5 10.7708L3.66667 16.1875Z"
      fill="#D1D5DB"
    />
  </svg>
</template>

<script>
export default {
  props: {
    className: {
      type: String,
      default: () => {},
    },
  },
}
</script>

<style scoped>
svg path {
  fill: currentColor;
}
</style>