<script setup lang="ts">
import type { DialogContentEmits, DialogContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DialogClose, DialogContent, DialogOverlay, DialogPortal, useForwardPropsEmits } from 'reka-ui'
import { IconButton } from '@/components/ui/icon-button'
import { cn } from '@/lib/utils'
import { drawerCloseButtonClasses, drawerContentClasses, drawerOverlayClasses, drawerSideClasses } from '.'

// Attributes (id, data-*, aria-*) go to the panel, not the portal.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<DialogContentProps & {
  /** Edge it slides in from */
  side?: 'top' | 'right' | 'bottom' | 'left'
  /** The close (×) button in the top-right corner */
  showCloseButton?: boolean
  class?: HTMLAttributes['class']
}>(), {
  side: 'right',
  showCloseButton: true,
})
const emits = defineEmits<DialogContentEmits>()
const delegated = reactiveOmit(props, 'class', 'side', 'showCloseButton')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <DialogPortal>
    <DialogOverlay
      data-slot="drawer-overlay"
      :class="drawerOverlayClasses"
    />
    <DialogContent
      data-slot="drawer-content"
      :data-side="side"
      v-bind="{ ...forwarded, ...$attrs }"
      :class="cn(drawerContentClasses, drawerSideClasses[side], props.class)"
    >
      <slot />
      <DialogClose v-if="showCloseButton" as-child>
        <IconButton icon="close" label="Close" hierarchy="tertiary" size="sm" :class="drawerCloseButtonClasses" />
      </DialogClose>
    </DialogContent>
  </DialogPortal>
</template>
