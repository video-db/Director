<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { itemActionsClasses } from './variants'

// Buttons, badges, a switch or a ⋮ menu at the end of the row.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="item-actions" :class="cn(itemActionsClasses, props.class)">
    <slot />
  </div>
</template>
