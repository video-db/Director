<script setup lang="ts">
import type { PopoverContentEmits, PopoverContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { PopoverContent, PopoverPortal, useForwardPropsEmits } from 'reka-ui'
import { cn } from '@/lib/utils'
import { popoverContentClasses } from '.'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<PopoverContentProps & { class?: HTMLAttributes['class'] }>(), {
  sideOffset: 4,
  align: 'center',
})
const emits = defineEmits<PopoverContentEmits>()
const delegated = reactiveOmit(props, 'class')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <PopoverPortal>
    <PopoverContent
      data-slot="popover-content"
      v-bind="{ ...forwarded, ...$attrs }"
      :class="cn(popoverContentClasses, 'origin-(--reka-popover-content-transform-origin)', props.class)"
    >
      <slot />
    </PopoverContent>
  </PopoverPortal>
</template>
