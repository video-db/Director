<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import {
  emptyStateClasses,
  emptyStateDescriptionClasses,
  emptyStateGlyphClasses,
  emptyStateIconClasses,
  emptyStateTextClasses,
  emptyStateTitleClasses,
} from '.'

// Put a Button in the default slot.
const props = withDefaults(defineProps<{
  title: string
  description?: string
  /** Material Symbols name */
  icon?: string
  /** Heading level of the title, to fit the page's outline */
  level?: 2 | 3 | 4 | 5 | 6
  class?: HTMLAttributes['class']
}>(), {
  icon: 'image',
  level: 3,
})
</script>

<template>
  <div
    data-slot="empty-state"
    :class="cn(emptyStateClasses, props.class)"
  >
    <span :class="emptyStateGlyphClasses">
      <Icon :name="icon" :size="32" :class="emptyStateIconClasses" />
    </span>
    <div :class="emptyStateTextClasses">
      <component :is="`h${level}`" :class="emptyStateTitleClasses">
        {{ title }}
      </component>
      <p v-if="description" :class="emptyStateDescriptionClasses">
        {{ description }}
      </p>
    </div>
    <slot />
  </div>
</template>
