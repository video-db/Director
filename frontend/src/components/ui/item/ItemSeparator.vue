<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { inject } from 'vue'
import { cn } from '@/lib/utils'
import { itemGroupKey, itemSeparatorClasses } from '.'

// A 1px line between rows. In an ItemGroup it is decoration only, since a list may hold only list items.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
const inGroup = inject(itemGroupKey, false)
</script>

<template>
  <div
    data-slot="item-separator"
    :role="inGroup ? 'none' : 'separator'"
    :aria-orientation="inGroup ? undefined : 'horizontal'"
    :aria-hidden="inGroup || undefined"
    :class="cn(itemSeparatorClasses, props.class)"
  />
</template>
