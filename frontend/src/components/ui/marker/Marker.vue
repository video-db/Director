<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import type { MarkerVariants } from '.'
import { Primitive } from 'reka-ui'
import { cn } from '@/lib/utils'
import { markerVariants } from '.'

// Presentational by default. Set role="status" for live progress ("Thinking…"), or render it as a
// link or button with as="a" / as="button" (or as-child) when it does something.
const props = withDefaults(defineProps<PrimitiveProps & {
  variant?: MarkerVariants['variant']
  class?: HTMLAttributes['class']
}>(), {
  as: 'div',
})
</script>

<template>
  <Primitive
    data-slot="marker"
    :data-variant="variant ?? 'default'"
    :as="as"
    :as-child="asChild"
    :type="as === 'button' && !asChild ? 'button' : undefined"
    :class="cn(markerVariants({ variant }), props.class)"
  >
    <slot />
  </Primitive>
</template>
