<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { InputVariants } from './variants'
import Input from './Input.vue'

// An Input with a search icon that shows a clear
// button while typing or filled.
const props = withDefaults(defineProps<{
  size?: InputVariants['size']
  placeholder?: string
  /** Accessible name (aria-label). An aria-label or aria-labelledby you pass wins. */
  label?: string
  disabled?: boolean
  class?: HTMLAttributes['class']
}>(), {
  label: 'Search',
})

const model = defineModel<string>({ default: '' })
</script>

<template>
  <!-- Attributes fall through to the native input after these, so a passed aria-label replaces label. -->
  <Input
    v-model="model"
    type="search"
    role="searchbox"
    leading-icon="search"
    clearable
    :size="size"
    :placeholder="placeholder ?? 'Search'"
    :aria-label="$attrs['aria-labelledby'] ? undefined : props.label"
    :disabled="disabled"
    :class="props.class"
  />
</template>
