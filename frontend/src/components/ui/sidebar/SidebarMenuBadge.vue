<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarMenuBadgeClasses } from '.'

// A count at the end of a menu item, e.g. unread messages. Hidden on the icon rail.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="sidebar-menu-badge" :class="cn(sidebarMenuBadgeClasses, props.class)">
    <slot />
  </div>
</template>
