<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { dialogBodyClasses } from '.'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <div
    data-slot="dialog-body"
    :class="cn(dialogBodyClasses, props.class)"
  >
    <slot />
  </div>
</template>
