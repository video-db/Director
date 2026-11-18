<script setup lang="ts">
import type { DialogContentEmits, DialogContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DialogContent, DialogOverlay, DialogPortal, useForwardPropsEmits } from 'reka-ui'
import { cn } from '@/lib/utils'
import type { DialogSize } from '.'
import { dialogSizes, overlayClasses, panelClasses } from '.'

// Attributes (id, data-*, aria-*) go to the panel, not the portal.
defineOptions({ inheritAttrs: false })

const props = defineProps<DialogContentProps & {
  /** Width: sm 500px (share), lg 620px, xl 720px (upload) */
  size?: DialogSize
  class?: HTMLAttributes['class']
}>()
const emits = defineEmits<DialogContentEmits>()
const delegated = reactiveOmit(props, 'class', 'size')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <DialogPortal>
    <DialogOverlay :class="overlayClasses" />
    <DialogContent
      data-slot="dialog-content"
      v-bind="{ ...forwarded, ...$attrs }"
      :class="cn(panelClasses, dialogSizes[size ?? 'sm'], props.class)"
    >
      <slot />
    </DialogContent>
  </DialogPortal>
</template>
