<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { itemContentClasses } from './variants'

// Takes the free space; a second ItemContent (e.g. a size or date column) only takes what it needs.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div
    data-slot="item-content"
    :class="cn(itemContentClasses, props.class)"
  >
    <slot />
  </div>
</template>
