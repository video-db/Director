<template>
  <div class="vdb-c-flex vdb-c-gap-4 vdb-c-items-center vdb-c-px-4" :class="baseClass">
    <div class="vdb-c-w-6 vdb-c-h-6 vdb-c-bg-white vdb-c-rounded-full dot"></div>
    <div class="vdb-c-w-6 vdb-c-h-6 vdb-c-bg-white vdb-c-rounded-full dot"></div>
    <div class="vdb-c-w-6 vdb-c-h-6 vdb-c-bg-white vdb-c-rounded-full dot"></div>
  </div>
</template>

<script>
export default {
  props: {
    baseClass: {
      type: String,
      default: '',
    },
  },
}
</script>

<style lang="scss" scoped>
.dot {
  display: inline-block;
  animation-name: bouncing;
  animation-duration: 700ms;
  animation-iteration-count: infinite;
  animation-timing-function: ease-out;
  &:nth-child(2) {
    animation-delay: 125ms;
  }
  &:nth-child(3) {
    animation-delay: 250ms;
  }
}

@keyframes bouncing {
  0% {
    transform: none;
  }

  33% {
    transform: translateY(-0.5em);
  }

  66% {
    transform: none;
  }
}
</style>