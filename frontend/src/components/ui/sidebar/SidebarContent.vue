<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarContentClasses } from '.'

// The part between the header and footer that scrolls. It holds the groups.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="sidebar-content" :class="cn(sidebarContentClasses, props.class)">
    <slot />
  </div>
</template>
