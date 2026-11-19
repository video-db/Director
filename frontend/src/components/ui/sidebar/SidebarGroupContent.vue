<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarGroupContentClasses } from '.'

// The body of a group, under its label: usually a SidebarMenu.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="sidebar-group-content" :class="cn(sidebarGroupContentClasses, props.class)">
    <slot />
  </div>
</template>
