<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { cardFooterBandClasses, cardFooterClasses, cardFooterLayouts } from './variants'

// inline: actions in line with the content. band: a grey strip across the bottom of the card, like DialogFooter.
// layout: "start" left-aligns the items; "actions" puts them on the right; "split" pushes the first item left.
const props = withDefaults(defineProps<{
  variant?: 'inline' | 'band'
  layout?: 'start' | 'actions' | 'split'
  class?: HTMLAttributes['class']
}>(), {
  variant: 'inline',
  layout: 'start',
})
</script>

<template>
  <div
    data-slot="card-footer"
    :data-variant="variant"
    :class="cn(cardFooterClasses, cardFooterLayouts[layout], variant === 'band' && cardFooterBandClasses, props.class)"
  >
    <slot />
  </div>
</template>
