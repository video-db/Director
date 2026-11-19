<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { fieldGroupClass } from './variants'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="field-group" :class="cn(fieldGroupClass, props.class)">
    <slot />
  </div>
</template>
