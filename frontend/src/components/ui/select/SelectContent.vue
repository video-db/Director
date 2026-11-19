<script setup lang="ts">
import type { SelectContentEmits, SelectContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { SelectContent, SelectPortal, SelectViewport, useForwardPropsEmits } from 'reka-ui'
import { cn } from '@/lib/utils'
import { selectContentClasses, selectViewportClasses } from '.'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<SelectContentProps & { class?: HTMLAttributes['class'] }>(), {
  position: 'popper',
  sideOffset: 4,
})
const emits = defineEmits<SelectContentEmits>()

const delegated = reactiveOmit(props, 'class')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <SelectPortal>
    <SelectContent
      data-slot="select-content"
      v-bind="{ ...forwarded, ...$attrs }"
      :class="cn(
        selectContentClasses,
        'max-h-(--reka-select-content-available-height) min-w-(--reka-select-trigger-width) origin-(--reka-select-content-transform-origin)',
        props.class,
      )"
    >
      <SelectViewport :class="selectViewportClasses">
        <slot />
      </SelectViewport>
    </SelectContent>
  </SelectPortal>
</template>
