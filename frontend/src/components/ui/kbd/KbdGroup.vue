<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { kbdGroupClass } from './variants'

// Keys pressed together or in sequence, e.g. ⌘ + K.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <kbd data-slot="kbd-group" :class="cn(kbdGroupClass, props.class)">
    <slot />
  </kbd>
</template>
