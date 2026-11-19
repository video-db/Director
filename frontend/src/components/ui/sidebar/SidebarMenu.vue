<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarMenuClasses } from '.'

// A list of SidebarMenuItems.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <ul data-slot="sidebar-menu" :class="cn(sidebarMenuClasses, props.class)">
    <slot />
  </ul>
</template>
