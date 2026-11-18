<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { injectSidebar } from './context'
import { sidebarRailClasses } from '.'

// A thin strip along the panel's inner edge: click it to collapse the panel, and to expand it again from the
// icon rail (a collapsed off-canvas panel is hidden, so the trigger brings it back). It is for the pointer only,
// so it is out of the Tab order and hidden from screen readers; the trigger and Cmd+B do the same.
const props = withDefaults(defineProps<{
  /** Tooltip on hover */
  label?: string
  class?: HTMLAttributes['class']
}>(), {
  label: 'Toggle sidebar',
})

const sidebar = injectSidebar('SidebarRail')
</script>

<template>
  <button
    v-if="!sidebar.isMobile.value && sidebar.collapsible.value !== 'none'"
    data-slot="sidebar-rail"
    type="button"
    tabindex="-1"
    aria-hidden="true"
    :title="label"
    :class="cn(sidebarRailClasses, props.class)"
    @click="sidebar.toggleSidebar()"
  />
</template>
