<template>
  <svg
    :class="className"
    width="20"
    height="20"
    viewBox="0 0 20 20"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <g clip-path="url(#clip0_3692_3159)">
      <path
        d="M15.8333 5.34166L14.6583 4.16666L9.99996 8.82499L5.34163 4.16666L4.16663 5.34166L8.82496 9.99999L4.16663 14.6583L5.34163 15.8333L9.99996 11.175L14.6583 15.8333L15.8333 14.6583L11.175 9.99999L15.8333 5.34166Z"
        :fill="topFill"
      />
    </g>
    <defs>
      <clipPath id="clip0_3692_3159">
        <rect width="20" height="20" fill="white" />
      </clipPath>
    </defs>
  </svg>
</template>

<script>
export default {
  name: "SearchCrossIcon",
  props: {
    className: {
      type: String,
      default: "",
    },
    topFill: {
      type: String,
      default: "#807E86",
    },
    bottomFill: {
      type: String,
      default: "#2D2D2D",
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
