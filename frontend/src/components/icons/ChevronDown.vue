<template>
  <div>
    <svg
      :class="className"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g id="Chevron down">
        <path
          id="Icon"
          d="M12.6668 6L8.00016 10.6667L3.3335 6"
          :stroke="strokeColor"
          :stroke-width="strokeWidth"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </g>
    </svg>
  </div>
</template>
<script>
export default {
  props: {
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
      default: "#1F2937",
    },
  },
};
</script>
