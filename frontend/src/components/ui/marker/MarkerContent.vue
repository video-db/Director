<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { markerContentClasses, markerContentShimmerClasses } from './variants'

const props = defineProps<{
  /** Animated shimmer for streaming text, e.g. "Thinking…". Stops with reduced motion. */
  shimmer?: boolean
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <span
    data-slot="marker-content"
    :class="cn(markerContentClasses, shimmer && markerContentShimmerClasses, props.class)"
  >
    <slot />
  </span>
</template>
