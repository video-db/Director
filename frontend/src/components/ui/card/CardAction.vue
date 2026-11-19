<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { cardActionClasses } from './variants'

// Top-right of the header, e.g. a "View usage" button or a ⋮ menu.
// It sits above a stretched title link, so it stays clickable on interactive cards.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div
    data-slot="card-action"
    :class="cn(cardActionClasses, props.class)"
  >
    <slot />
  </div>
</template>
