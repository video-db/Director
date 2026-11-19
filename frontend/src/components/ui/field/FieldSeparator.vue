<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { fieldSeparatorClass } from './variants'

// Visual only: the fieldsets on either side name their own groups.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div data-slot="field-separator" aria-hidden="true" :class="cn(fieldSeparatorClass, props.class)" />
</template>
