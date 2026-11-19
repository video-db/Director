<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarFooterClasses } from '.'

// Pinned below the content: an account menu or settings.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="sidebar-footer" :class="cn(sidebarFooterClasses, props.class)">
    <slot />
  </div>
</template>
