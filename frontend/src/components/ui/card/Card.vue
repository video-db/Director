<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import type { CardVariants } from './variants'
import { Primitive } from 'reka-ui'
import { cn } from '@/lib/utils'
import { cardVariants } from './variants'

// Render it as a <section> or <article> with as="…" when the card is a landmark or a standalone item.
const props = withDefaults(defineProps<PrimitiveProps & {
  /** md: 20px between and around parts. sm: 16px, and a smaller title. */
  size?: CardVariants['size']
  variant?: CardVariants['variant']
  /** Hover and focus styles for a card whose title is a stretched link */
  interactive?: boolean
  class?: HTMLAttributes['class']
}>(), {
  as: 'div',
  size: 'md',
})
</script>

<template>
  <Primitive
    data-slot="card"
    :data-size="size"
    :as="as"
    :as-child="asChild"
    :class="cn(cardVariants({ size, variant, interactive }), props.class)"
  >
    <slot />
  </Primitive>
</template>
