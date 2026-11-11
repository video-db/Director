<template>
  <div>
    <svg
      :class="className"
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fill-rule="evenodd"
        clip-rule="evenodd"
        d="M10 3.33464C6.31812 3.33464 3.33335 6.3194 3.33335 10.0013C3.33335 13.6832 6.31812 16.668 10 16.668C13.6819 16.668 16.6667 13.6832 16.6667 10.0013C16.6667 6.3194 13.6819 3.33464 10 3.33464ZM1.66669 10.0013C1.66669 5.39893 5.39765 1.66797 10 1.66797C14.6024 1.66797 18.3334 5.39893 18.3334 10.0013C18.3334 14.6037 14.6024 18.3346 10 18.3346C5.39765 18.3346 1.66669 14.6037 1.66669 10.0013Z"
        fill="#12131A"
      />
      <path
        fill-rule="evenodd"
        clip-rule="evenodd"
        d="M8.57739 6.91205C8.90283 6.58661 9.43047 6.58661 9.7559 6.91205L12.2559 9.41205C12.5813 9.73748 12.5813 10.2651 12.2559 10.5906L9.7559 13.0906C9.43047 13.416 8.90283 13.416 8.57739 13.0906C8.25195 12.7651 8.25195 12.2375 8.57739 11.912L10.4881 10.0013L8.57739 8.09056C8.25195 7.76512 8.25195 7.23748 8.57739 6.91205Z"
        fill="#12131A"
      />
    </svg>
  </div>
</template>
<script>
export default {
  name: "ChevronRightCircledIcon",
  props: {
    className: {
      type: String,
      default: "",
    },
    fill: {
      type: String,
      default: "black",
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
