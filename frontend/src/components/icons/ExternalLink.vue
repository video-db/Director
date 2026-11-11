<template>
  <div>
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clip-path="url(#clip0_1351_16008)">
        <path
          d="M5.5 2.5H2.5C1.67157 2.5 1 3.17157 1 4V11.5C1 12.3284 1.67157 13 2.5 13H10C10.8284 13 11.5 12.3284 11.5 11.5V8.5M8.5 1H13M13 1V5.5M13 1L5.5 8.5"
          stroke="#111827"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </g>
      <defs>
        <clipPath id="clip0_1351_16008">
          <rect width="14" height="14" fill="white" />
        </clipPath>
      </defs>
    </svg>
  </div>
</template>
<script>
export default {
  name: "ExternalLinkIcon",
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
  stroke: currentColor;
}
</style>
