<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { Primitive } from 'reka-ui'
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarMenuSubButtonClasses } from '.'

// A nested item. A link by default: give it an href, use as="button", or as-child around your router's link.
const props = withDefaults(defineProps<PrimitiveProps & {
  /** The current page: a grey fill, medium text and aria-current="page" */
  active?: boolean
  /** Ignores clicks and Enter; a link is taken out of the Tab order */
  disabled?: boolean
  size?: 'sm' | 'md'
  class?: HTMLAttributes['class']
}>(), {
  as: 'a',
  size: 'md',
})

const isButton = computed(() => !props.asChild && props.as === 'button')
function blockClick(e: MouseEvent) {
  if (!props.disabled) return
  e.preventDefault()
  e.stopImmediatePropagation()
}
</script>

<template>
  <Primitive
    data-slot="sidebar-menu-sub-button"
    :as="as"
    :as-child="asChild"
    :type="isButton ? ($attrs.type ?? 'button') : undefined"
    :data-size="size"
    :data-active="active ? '' : undefined"
    :aria-current="active ? 'page' : undefined"
    :aria-disabled="disabled || undefined"
    :disabled="isButton ? disabled : undefined"
    :tabindex="disabled && !isButton ? -1 : undefined"
    :class="cn(sidebarMenuSubButtonClasses, props.class)"
    @click.capture="blockClick"
  >
    <slot />
  </Primitive>
</template>
