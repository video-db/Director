<script setup lang="ts">
import type { TooltipContentEmits, TooltipContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TooltipArrow, TooltipContent, TooltipPortal, useForwardPropsEmits } from 'reka-ui'
import { cn } from '@/lib/utils'
import { tooltipArrowClasses, tooltipContentClasses } from '.'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<TooltipContentProps & {
  /** Show a small arrow pointing at the trigger */
  arrow?: boolean
  class?: HTMLAttributes['class']
}>(), {
  sideOffset: 6,
})
const emits = defineEmits<TooltipContentEmits>()
const delegated = reactiveOmit(props, 'class', 'arrow')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <TooltipPortal>
    <TooltipContent
      data-slot="tooltip-content"
      v-bind="{ ...forwarded, ...$attrs }"
      :class="cn(tooltipContentClasses, 'origin-(--reka-tooltip-content-transform-origin)', props.class)"
    >
      <slot />
      <TooltipArrow v-if="arrow" :width="10" :height="5" :class="tooltipArrowClasses" />
    </TooltipContent>
  </TooltipPortal>
</template>
