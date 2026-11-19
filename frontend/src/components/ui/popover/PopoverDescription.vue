<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { popoverDescriptionClasses } from './variants'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <p data-slot="popover-description" :class="cn(popoverDescriptionClasses, props.class)">
    <slot />
  </p>
</template>
