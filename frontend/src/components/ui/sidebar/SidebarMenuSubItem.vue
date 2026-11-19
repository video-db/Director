<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarMenuSubItemClasses } from '.'

// One nested row, holding a SidebarMenuSubButton.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <li data-slot="sidebar-menu-sub-item" :class="cn(sidebarMenuSubItemClasses, props.class)">
    <slot />
  </li>
</template>
