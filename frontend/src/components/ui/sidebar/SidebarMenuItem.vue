<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarMenuItemClasses } from '.'

// One row: a SidebarMenuButton, and optionally a SidebarMenuAction, a SidebarMenuBadge or a SidebarMenuSub.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <li data-slot="sidebar-menu-item" :class="cn(sidebarMenuItemClasses, props.class)">
    <slot />
  </li>
</template>
