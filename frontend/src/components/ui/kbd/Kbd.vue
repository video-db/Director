<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { KbdVariants } from '.'
import { cn } from '@/lib/utils'
import { kbdVariants } from '.'

const props = defineProps<{
  /** inverse inside Tooltip and other dark surfaces */
  variant?: KbdVariants['variant']
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <kbd data-slot="kbd" :class="cn(kbdVariants({ variant }), props.class)">
    <slot />
  </kbd>
</template>
