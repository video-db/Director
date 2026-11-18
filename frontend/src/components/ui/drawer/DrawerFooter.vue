<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { drawerFooterClasses } from '.'

// Pinned to the bottom of the drawer. Buttons stack full width; add flex-row to put them side by side.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="drawer-footer" :class="cn(drawerFooterClasses, props.class)">
    <slot />
  </div>
</template>
