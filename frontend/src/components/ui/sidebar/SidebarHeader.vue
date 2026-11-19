<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarHeaderClasses } from '.'

// Pinned above the content: a workspace switcher, a logo or a search field.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="sidebar-header" :class="cn(sidebarHeaderClasses, props.class)">
    <slot />
  </div>
</template>
