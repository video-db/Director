<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { PillVariants } from './variants'
import { cn } from '@/lib/utils'
import { counterClasses, counterTones, pillVariants } from './variants'

// A fully rounded count, e.g. next to a section title.
const props = defineProps<{
  count: number | string
  colour?: 'neutral' | 'brand'
  emphasis?: 'subtle' | 'bold'
  size?: PillVariants['size']
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <span
    data-slot="counter"
    :class="cn(pillVariants({ size }), counterClasses, counterTones[`${colour ?? 'neutral'}-${emphasis ?? 'subtle'}`], props.class)"
  >
    {{ count }}
  </span>
</template>
