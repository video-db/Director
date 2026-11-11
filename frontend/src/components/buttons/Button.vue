<template>
  <button
    :class="[
      'vdb-c-flex vdb-c-rounded-lg vdb-c-px-16 vdb-c-py-8 vdb-c-transition-colors vdb-c-duration-300 vdb-c-ease-in-out',
      {
        'hover:vdb-c-bg-ota vdb-c-bg-black vdb-c-text-white':
          variant === 'primary',
        'vdb-c-border-pam hover:vdb-c-border-pam hover:vdb-c-bg-pam vdb-c-border vdb-c-bg-white vdb-c-text-black hover:vdb-c-text-white':
          variant === 'secondary',
        'vdb-c-bg-orange vdb-c-text-white hover:vdb-c-bg-orange-400':
          variant === 'tertiary',
      },
    ]"
  >
    <slot />
  </button>
</template>

<script setup>
import { defineProps } from "vue";

defineProps({
  variant: {
    type: String,
    default: "primary",
    validator: (value) => ["primary", "secondary", "tertiary"].includes(value),
  },
});
</script>
