<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { provide } from 'vue'
import { cn } from '@/lib/utils'
import { itemGroupClasses, itemGroupKey } from '.'

// A list of items. Each Item inside is wrapped in a list item; separators are hidden from screen readers.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
provide(itemGroupKey, true)
</script>

<template>
  <div data-slot="item-group" role="list" :class="cn(itemGroupClasses, props.class)">
    <slot />
  </div>
</template>
