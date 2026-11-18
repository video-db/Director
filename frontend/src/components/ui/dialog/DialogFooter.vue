<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import type { DialogFooterLayout } from '.'
import { dialogFooterClasses, dialogFooterLayouts } from '.'

const props = withDefaults(defineProps<{
  layout?: DialogFooterLayout
  class?: HTMLAttributes['class']
}>(), {
  layout: 'actions',
})
</script>

<template>
  <div
    data-slot="dialog-footer"
    :class="cn(dialogFooterClasses, dialogFooterLayouts[layout], props.class)"
  >
    <slot />
  </div>
</template>
