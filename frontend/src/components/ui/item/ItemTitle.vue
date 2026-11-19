<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { Primitive } from 'reka-ui'
import { cn } from '@/lib/utils'
import { itemTitleClasses } from './variants'

// Use as="label" with :for to name a switch or checkbox in the row, or as="h3" for a heading.
const props = withDefaults(defineProps<PrimitiveProps & { class?: HTMLAttributes['class'] }>(), {
  as: 'div',
})
</script>

<template>
  <Primitive
    data-slot="item-title"
    :as="as"
    :as-child="asChild"
    :class="cn(itemTitleClasses, props.class)"
  >
    <slot />
  </Primitive>
</template>
