<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Counter } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { sectionHeaderActionClasses, sectionHeaderClasses, sectionHeaderDescriptionClasses, sectionHeaderTextClasses, sectionHeaderTitleClasses, sectionHeaderTitleRowClasses } from './variants'

// Put a button or link in #action.
const props = withDefaults(defineProps<{
  title: string
  /** Sub copy under the title */
  description?: string
  /** Shows a counter next to the title */
  count?: number | string
  /** Heading level for the title */
  as?: 'h2' | 'h3' | 'h4'
  class?: HTMLAttributes['class']
}>(), {
  as: 'h2',
})
</script>

<template>
  <div data-slot="section-header" :class="cn(sectionHeaderClasses, props.class)">
    <div :class="sectionHeaderTextClasses">
      <div :class="sectionHeaderTitleRowClasses">
        <component :is="as" :class="sectionHeaderTitleClasses">
          {{ title }}
        </component>
        <Counter v-if="count !== undefined" :count="count" size="sm" />
      </div>
      <p v-if="description" :class="sectionHeaderDescriptionClasses">
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.action" :class="sectionHeaderActionClasses">
      <slot name="action" />
    </div>
  </div>
</template>
