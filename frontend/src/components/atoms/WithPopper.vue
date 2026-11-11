<template>
  <popper
    hover
    arrow
    :placement="toolTipPlacement"
    :modifiers="{ offset: { offset: '0,10px' } }"
    boundaries="30px"
  >
    <template
      #content
      class="small-font vdb-c-hidden sm:vdb-c-block"
      :class="tooltipCss"
    >
      {{ popperText }}
    </template>
    <div slot="reference"><slot name="button" /></div>
  </popper>
</template>

<script setup>
import Popper from "vue3-popper";

defineProps({
  popperText: {
    type: String,
    default: "",
  },
  toolTipPlacement: {
    type: String,
    default: "top",
  },
  tooltipCss: {
    type: String,
    default: "",
  },
});
</script>
<style scoped>
.small-font {
  font-size: 10px;
}
</style>
