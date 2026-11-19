<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { InputGroupAddonAlign } from '.'
import { computed, inject } from 'vue'
import { Icon } from '@/components/ui/icon'
import { inputIconSize } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { inputGroupAddonAlignClasses, inputGroupAddonClasses, inputGroupKey } from '.'

// Holds an icon, InputGroupText, InputGroupButtons or a Kbd. Its place is set by `align`, not by
// where it sits in the markup, so the control can come first and keep a natural reading order.
const props = withDefaults(defineProps<{
  align?: InputGroupAddonAlign
  /** Material Symbols name. Sized to the group: 16 at sm, 20 at md, 24 at lg (as in Input). */
  icon?: string
  class?: HTMLAttributes['class']
}>(), {
  align: 'inline-start',
})

const group = inject(inputGroupKey, null)
const size = computed(() => group?.size.value ?? 'lg')
const iconSize = computed(() => inputIconSize[size.value])
const block = computed(() => props.align === 'block-start' || props.align === 'block-end')

// A button at the outer edge is pulled outwards so it sits 4px from the border; the leading icon
// turns red when invalid, as in Input (inputGroupAddonAlignClasses).
const alignClass = computed(() => inputGroupAddonAlignClasses(props.align, size.value))

// Clicking the addon (not a button in it) focuses the control, as clicking a label would.
function focusControl(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('button, a, input, textarea, select')) return
  const root = (e.currentTarget as HTMLElement).closest('[data-slot="input-group"]')
  root?.querySelector<HTMLElement>('[data-slot="input-group-control"]')?.focus()
}
</script>

<template>
  <div
    data-slot="input-group-addon"
    :data-align="align"
    :data-block="block ? '' : undefined"
    :class="cn(inputGroupAddonClasses, alignClass, props.class)"
    @click="focusControl"
  >
    <Icon v-if="icon" :name="icon" :size="iconSize" />
    <slot />
  </div>
</template>
