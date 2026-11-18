<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarSeparatorClasses } from '.'

// A 1px line between groups, or between the header and the content.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="sidebar-separator" role="separator" :class="cn(sidebarSeparatorClasses, props.class)" />
</template>
