<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { cardDescriptionClasses } from './variants'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <p data-slot="card-description" :class="cn(cardDescriptionClasses, props.class)">
    <slot />
  </p>
</template>
