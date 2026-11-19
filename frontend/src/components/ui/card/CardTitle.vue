<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { Primitive } from 'reka-ui'
import { cn } from '@/lib/utils'
import { cardTitleClasses } from './variants'

// A heading by default. Pick the level that fits the page with as="h2" / "h4"…
const props = withDefaults(defineProps<PrimitiveProps & { class?: HTMLAttributes['class'] }>(), {
  as: 'h3',
})
</script>

<template>
  <Primitive
    data-slot="card-title"
    :as="as"
    :as-child="asChild"
    :class="cn(cardTitleClasses, props.class)"
  >
    <slot />
  </Primitive>
</template>
