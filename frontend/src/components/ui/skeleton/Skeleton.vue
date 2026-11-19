<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { skeletonClasses } from './variants'

// A placeholder block. Size and shape it with classes (h-20 w-[60%], rounded-full…).
// It is hidden from screen readers: the region it sits in says it is loading.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div
    data-slot="skeleton"
    aria-hidden="true"
    :class="cn(skeletonClasses, props.class)"
  />
</template>
