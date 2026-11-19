<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { cardHeaderClasses } from './variants'

// Title and description stack; a CardAction sits top-right, spanning both rows.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div
    data-slot="card-header"
    :class="cn(cardHeaderClasses, props.class)"
  >
    <slot />
  </div>
</template>
