<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { iconStyle } from './variants'

const props = withDefaults(defineProps<{
  /** Material Symbols name, e.g. "search" or "cloud_upload" */
  name: string
  /** Size in px: 12, 16, 20 (default) or 24 */
  size?: number
  filled?: boolean
  class?: HTMLAttributes['class']
}>(), {
  size: 20,
  filled: false,
})

const style = computed(() => iconStyle(props.size, props.filled))
</script>

<template>
  <span
    data-slot="icon"
    aria-hidden="true"
    :class="cn('material-symbols-outlined', props.class)"
    :style="style"
  >{{ name }}</span>
</template>
