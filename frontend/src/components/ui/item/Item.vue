<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { FunctionalComponent, HTMLAttributes } from 'vue'
import type { ItemVariants } from '.'
import { Primitive } from 'reka-ui'
import { h, inject } from 'vue'
import { cn } from '@/lib/utils'
import { itemGroupKey, itemListItemClasses, itemVariants } from '.'

// A generic row: media, title and description, actions. Render it as a link or button with
// as="a" / as="button", or as-child around NuxtLink, to get hover and focus styles.
// Extra attributes (href, type, aria-*…) go to the row itself, not the list item around it.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<PrimitiveProps & {
  variant?: ItemVariants['variant']
  size?: ItemVariants['size']
  class?: HTMLAttributes['class']
}>(), {
  as: 'div',
})

// Inside an ItemGroup the row is wrapped in a list item, so links and buttons keep their own role.
const inGroup = inject(itemGroupKey, false)
const ListItem: FunctionalComponent = (_, { slots }) =>
  inGroup ? h('div', { role: 'listitem', class: itemListItemClasses }, slots.default?.()) : slots.default?.()
</script>

<template>
  <ListItem>
    <Primitive
      :type="as === 'button' && !asChild ? 'button' : undefined"
      v-bind="$attrs"
      data-slot="item"
      :as="as"
      :as-child="asChild"
      :class="cn(itemVariants({ variant, size }), props.class)"
    >
      <slot />
    </Primitive>
  </ListItem>
</template>
