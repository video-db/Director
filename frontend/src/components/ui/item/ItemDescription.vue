<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { itemDescriptionClasses } from './variants'

// Clamped to two lines. Give it an id and point the row's control at it with aria-describedby.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <p data-slot="item-description" :class="cn(itemDescriptionClasses, props.class)">
    <slot />
  </p>
</template>
