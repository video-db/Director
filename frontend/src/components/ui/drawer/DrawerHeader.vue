<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { drawerHeaderClasses } from '.'

// Holds DrawerTitle and DrawerDescription at the top of the drawer.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="drawer-header" :class="cn(drawerHeaderClasses, props.class)">
    <slot />
  </div>
</template>
