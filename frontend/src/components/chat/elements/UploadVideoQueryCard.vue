<template>
  <div
    class="vdb-c-flex vdb-c-flex-col vdb-c-gap-4 vdb-c-break-words vdb-c-text-kilvish-900"
  >
    <div class="vdb-c-flex vdb-c-items-center vdb-c-gap-4">
      Click here to see an example query &rarr;
    </div>
  </div>
</template>

<script>
export default {
  props: {
    ytLink: {
      type: String,
      default: "https://www.youtube.com/watch?v=FgrO9ADPZSA",
    },
  },
};
</script>
