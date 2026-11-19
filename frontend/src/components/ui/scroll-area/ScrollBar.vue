<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { ScrollAreaScrollbar, ScrollAreaThumb } from 'reka-ui'
import { cn } from '@/lib/utils'
import { scrollBarClasses, scrollBarOrientationClasses, scrollBarThumbClasses } from './variants'

// ScrollArea adds these for you; use ScrollBar directly only when building on Reka's ScrollAreaRoot.
// With type="hover" (the default) the bar fades in while the pointer is over the area.
const props = withDefaults(defineProps<{
  orientation?: 'vertical' | 'horizontal'
  class?: HTMLAttributes['class']
}>(), {
  orientation: 'vertical',
})
</script>

<template>
  <ScrollAreaScrollbar
    data-slot="scroll-area-scrollbar"
    :orientation="orientation"
    :class="cn(scrollBarClasses, scrollBarOrientationClasses[orientation], props.class)"
  >
    <ScrollAreaThumb
      data-slot="scroll-area-thumb"
      :class="cn(scrollBarThumbClasses)"
    />
  </ScrollAreaScrollbar>
</template>
