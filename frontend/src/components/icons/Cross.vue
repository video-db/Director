<template>
  <svg
    width="10"
    height="10"
    viewBox="0 0 10 10"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="className"
  >
    <path
      d="M3.64897 4.85103L0 8.5L1.20208 9.70208L4.85105 6.05311L8.50002 9.70208L9.70211 8.5L6.05313 4.85103L9.70208 1.20208L8.5 0L4.85105 3.64895L1.20211 0L2.43187e-05 1.20208L3.64897 4.85103Z"
      :fill="fill"
    />
  </svg>
</template>

<script>
export default {
  name: "Cross",
  props: {
    className: {
      type: String,
      default: "",
    },
    fill: {
      type: String,
      default: "#969696",
    },
  },
};
</script>
