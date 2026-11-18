<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { popoverHeaderClasses } from './variants'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="popover-header" :class="cn(popoverHeaderClasses, props.class)">
    <slot />
  </div>
</template>
