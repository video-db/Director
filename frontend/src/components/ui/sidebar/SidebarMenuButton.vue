<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import type { SidebarMenuButtonVariants } from '.'
import { Primitive } from 'reka-ui'
import { computed, inject, mergeProps, useAttrs } from 'vue'
import { Icon } from '@/components/ui/icon'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { sidebarKey } from './context'
import { sidebarMenuButtonVariants } from '.'

// A menu item's button. Render it as a link with as="a", or with as-child around your router's link
// (put the Icon inside the link then). Make it a CollapsibleTrigger's or DropdownMenuTrigger's element
// with as-child on the trigger. Attributes go to the button or link.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<PrimitiveProps & {
  /** Material Symbols name, before the label */
  icon?: string
  /** The current page: a grey fill, medium text and aria-current="page" */
  active?: boolean
  disabled?: boolean
  variant?: SidebarMenuButtonVariants['variant']
  /** sm 28 · md 32 · lg 48, for two lines with a logo or avatar */
  size?: SidebarMenuButtonVariants['size']
  /** Shown to the right while the sidebar is collapsed to icons, where the label is hidden */
  tooltip?: string
  class?: HTMLAttributes['class']
}>(), {
  as: 'button',
  variant: 'default',
  size: 'md',
})

// It works outside a SidebarProvider too, e.g. a list in a Scroll Area; the tooltip then never shows
const sidebar = inject(sidebarKey, null)
const attrs = useAttrs()

// A disabled button is natively disabled; a link is taken out of the Tab order and ignores clicks.
const isButton = computed(() => !props.asChild && props.as === 'button')
function blockClick(e: MouseEvent) {
  if (!props.disabled) return
  e.preventDefault()
  e.stopImmediatePropagation()
}
// Attributes passed in win, as in React, and a passed click handler runs as well as ours
const bound = computed(() => mergeProps({
  'data-size': props.size,
  'data-active': props.active ? '' : undefined,
  'aria-current': props.active ? 'page' as const : undefined,
  'aria-disabled': props.disabled || undefined,
  'disabled': isButton.value ? props.disabled : undefined,
  'tabindex': props.disabled && !isButton.value ? -1 : undefined,
  'type': isButton.value ? (attrs.type ?? 'button') : undefined,
  'class': cn(sidebarMenuButtonVariants({ variant: props.variant, size: props.size }), props.class),
  'onClickCapture': blockClick,
}, attrs))
// Only on the icon rail, where the label is hidden
const tooltipOff = computed(() => !sidebar || sidebar.state.value !== 'collapsed' || sidebar.collapsible.value !== 'icon' || sidebar.isMobile.value)
</script>

<template>
  <Tooltip v-if="tooltip" :disabled="tooltipOff">
    <TooltipTrigger as-child>
      <Primitive :as="as" :as-child="asChild" v-bind="bound" data-slot="sidebar-menu-button">
        <Icon v-if="icon && !asChild" :name="icon" />
        <slot />
      </Primitive>
    </TooltipTrigger>
    <TooltipContent side="right" align="center">
      {{ tooltip }}
    </TooltipContent>
  </Tooltip>
  <Primitive v-else :as="as" :as-child="asChild" v-bind="bound" data-slot="sidebar-menu-button">
    <Icon v-if="icon && !asChild" :name="icon" />
    <slot />
  </Primitive>
</template>
