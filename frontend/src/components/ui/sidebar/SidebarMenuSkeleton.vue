<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { sidebarMenuSkeletonClasses, sidebarMenuSkeletonIconClasses, sidebarMenuSkeletonTextClasses } from '.'

// A placeholder row while the menu loads. Vary the width down a list so it reads as text.
const props = withDefaults(defineProps<{
  /** A square for the icon before the text */
  showIcon?: boolean
  /** The text bar's width, as a CSS length */
  width?: string
  class?: HTMLAttributes['class']
}>(), {
  width: '70%',
})
</script>

<template>
  <div data-slot="sidebar-menu-skeleton" :class="cn(sidebarMenuSkeletonClasses, props.class)">
    <Skeleton v-if="showIcon" :class="sidebarMenuSkeletonIconClasses" />
    <Skeleton :class="sidebarMenuSkeletonTextClasses" :style="{ maxWidth: width }" />
  </div>
</template>
