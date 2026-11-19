<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarMenuSubClasses } from '.'

// Nested items under a menu item, hidden on the icon rail.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <ul data-slot="sidebar-menu-sub" :class="cn(sidebarMenuSubClasses, props.class)">
    <slot />
  </ul>
</template>
