<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { Icon } from '@/components/ui/icon'
import { IconButton } from '@/components/ui/icon-button'
import { cn } from '@/lib/utils'
import { injectSidebar } from './context'
import { sidebarTriggerClasses } from '.'

// Toggles the sidebar: the panel on wide screens, the drawer on small ones. A click handler passed in
// runs as well.
const props = withDefaults(defineProps<{
  /** Accessible name. aria-expanded says whether the sidebar is open. */
  label?: string
  class?: HTMLAttributes['class']
}>(), {
  label: 'Toggle sidebar',
})

const sidebar = injectSidebar('SidebarTrigger')
// A panel that never collapses is always expanded
const expanded = computed(() => sidebar.collapsible.value === 'none' || (sidebar.isMobile.value ? sidebar.openMobile.value : sidebar.open.value))
</script>

<template>
  <!-- The slot keeps the 20px icon; IconButton sm would draw 16 -->
  <IconButton
    data-slot="sidebar-trigger"
    icon="dock_to_right"
    :label="label"
    hierarchy="tertiary"
    size="sm"
    :aria-expanded="expanded"
    :aria-controls="sidebar.isMobile.value ? undefined : sidebar.panelId"
    :class="cn(sidebarTriggerClasses, props.class)"
    @click="sidebar.toggleSidebar()"
  >
    <slot>
      <Icon name="dock_to_right" />
    </slot>
  </IconButton>
</template>
