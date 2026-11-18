<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { alertDescriptionClasses } from './variants'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="alert-description" :class="cn(alertDescriptionClasses, props.class)">
    <slot />
  </div>
</template>
