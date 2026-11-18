<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { sidebarMenuActionClasses, sidebarMenuActionHoverClasses } from '.'

// A 24px icon button at the end of a menu item, after its SidebarMenuButton, e.g. a more_horiz menu
// (as a DropdownMenuTrigger's element). Hidden on the icon rail.
const props = defineProps<{
  /** Material Symbols name */
  icon: string
  /** Required: says what it does, e.g. "More for Design" */
  label: string
  /** Hidden until the item is hovered or has focus; shown while its menu is open, on the active item and on touch screens */
  showOnHover?: boolean
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <button
    data-slot="sidebar-menu-action"
    type="button"
    :aria-label="label"
    :class="cn(sidebarMenuActionClasses, showOnHover && sidebarMenuActionHoverClasses, props.class)"
  >
    <slot>
      <Icon :name="icon" :size="16" />
    </slot>
  </button>
</template>
