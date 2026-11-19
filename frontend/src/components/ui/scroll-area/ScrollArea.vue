<script setup lang="ts">
import type { ScrollAreaRootProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { ScrollAreaCorner, ScrollAreaRoot, ScrollAreaViewport } from 'reka-ui'
import { onMounted, ref } from 'vue'
import { cn } from '@/lib/utils'
import ScrollBar from './ScrollBar.vue'
import { scrollAreaClasses, scrollAreaViewportClasses } from './variants'

// A scrolling region with thin custom scrollbars. Give it a height (or width, for horizontal) with class.
// The viewport is always a Tab stop (Reka sets tabindex 0), so the arrow keys can scroll it;
// label names it as a region for screen readers.
const props = withDefaults(defineProps<Pick<ScrollAreaRootProps, 'type' | 'scrollHideDelay' | 'dir'> & {
  /** Which scrollbars to show */
  orientation?: 'vertical' | 'horizontal' | 'both'
  /** Accessible name for the scrolling region, e.g. "Your chats" */
  label?: string
  /** Classes for the viewport, e.g. padding around the content */
  viewportClass?: HTMLAttributes['class']
  class?: HTMLAttributes['class']
}>(), {
  type: 'hover',
  orientation: 'vertical',
})

const viewport = ref<InstanceType<typeof ScrollAreaViewport>>()
// e.g. scroll a chat list back to the top: scrollAreaRef.value.viewport?.viewportElement.scrollTo({ top: 0 })
defineExpose({ viewport })

if (import.meta.env.DEV) {
  onMounted(() => {
    if (!props.label)
      console.warn('[ScrollArea] The viewport is a Tab stop with no name: pass `label`, e.g. label="Your chats".')
  })
}
</script>

<template>
  <ScrollAreaRoot
    data-slot="scroll-area"
    :type="type"
    :scroll-hide-delay="scrollHideDelay"
    :dir="dir"
    :class="cn(scrollAreaClasses, props.class)"
  >
    <ScrollAreaViewport
      ref="viewport"
      data-slot="scroll-area-viewport"
      :role="label ? 'region' : undefined"
      :aria-label="label"
      :class="cn(scrollAreaViewportClasses, viewportClass)"
    >
      <slot />
    </ScrollAreaViewport>
    <ScrollBar v-if="orientation !== 'horizontal'" orientation="vertical" />
    <ScrollBar v-if="orientation !== 'vertical'" orientation="horizontal" />
    <ScrollAreaCorner v-if="orientation === 'both'" />
  </ScrollAreaRoot>
</template>
