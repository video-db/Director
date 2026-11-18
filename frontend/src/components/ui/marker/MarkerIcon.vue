<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { markerIconClasses } from './variants'

// Decorative: hidden from screen readers, so MarkerContent carries the meaning. Put an <Icon :size="16">
// or a <Spinner size="sm" decorative> inside.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <span
    data-slot="marker-icon"
    aria-hidden="true"
    :class="cn(markerIconClasses, props.class)"
  >
    <slot />
  </span>
</template>
