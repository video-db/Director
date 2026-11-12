<template>
  <svg
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="className"
  >
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M11.4941 11.4941C11.8195 11.1686 12.3472 11.1686 12.6726 11.4941L17.2559 16.0774C17.5814 16.4028 17.5814 16.9305 17.2559 17.2559C16.9305 17.5814 16.4028 17.5814 16.0774 17.2559L11.4941 12.6726C11.1686 12.3472 11.1686 11.8195 11.4941 11.4941Z"
      fill="white"
    />
    <path
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M8.33333 4.16667C6.03215 4.16667 4.16667 6.03215 4.16667 8.33333C4.16667 10.6345 6.03215 12.5 8.33333 12.5C10.6345 12.5 12.5 10.6345 12.5 8.33333C12.5 6.03215 10.6345 4.16667 8.33333 4.16667ZM2.5 8.33333C2.5 5.11167 5.11167 2.5 8.33333 2.5C11.555 2.5 14.1667 5.11167 14.1667 8.33333C14.1667 11.555 11.555 14.1667 8.33333 14.1667C5.11167 14.1667 2.5 11.555 2.5 8.33333Z"
      fill="white"
    />
  </svg>
</template>

<script>
export default {
  name: "SearchIcon",
  props: {
    className: {
      type: String,
      default: "",
    },
    fill: {
      type: String,
      default: "#FFF5EC",
    },
  },
};
</script>

<style scoped>
svg path {
  color: currentColor;
  fill: currentColor;
}
</style>
