<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { PillVariants } from './variants'
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { badgeVariants, pillDotClasses, pillDotSize, pillVariants, statusPillColours, statusPillLabel } from './variants'

// A fully rounded subtle badge with a status dot.
const props = defineProps<{
  status: 'active' | 'invited' | 'pending' | 'paid' | 'rejected' | 'failed'
  size?: PillVariants['size']
  class?: HTMLAttributes['class']
}>()

const label = computed(() => statusPillLabel(props.status))
</script>

<template>
  <span
    data-slot="status-pill"
    :class="cn(pillVariants({ size }), badgeVariants({ colour: statusPillColours[status], emphasis: 'subtle' }), 'rounded-full', props.class)"
  >
    <span aria-hidden="true" :class="[pillDotClasses, pillDotSize[size ?? 'md']]" />
    <slot>{{ label }}</slot>
  </span>
</template>
