<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { inputGroupTextClasses } from './variants'

// Fixed text in an addon, such as "https://", ".mp4" or "USD".
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <span
    data-slot="input-group-text"
    :class="cn(inputGroupTextClasses, props.class)"
  >
    <slot />
  </span>
</template>
