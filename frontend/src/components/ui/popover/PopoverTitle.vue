<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { popoverTitleClasses } from './variants'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="popover-title" :class="cn(popoverTitleClasses, props.class)">
    <slot />
  </div>
</template>
