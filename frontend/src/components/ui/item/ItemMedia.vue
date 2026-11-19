<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { ItemMediaVariants } from '.'
import { cn } from '@/lib/utils'
import { itemMediaVariants } from '.'

// icon: a 40px tile for an <Icon>. image: a 40px thumbnail for an <img>. default: as is, e.g. an <Avatar>.
const props = defineProps<{
  variant?: ItemMediaVariants['variant']
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div data-slot="item-media" :data-variant="variant ?? 'default'" :class="cn(itemMediaVariants({ variant }), props.class)">
    <slot />
  </div>
</template>
