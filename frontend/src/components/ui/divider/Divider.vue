<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
import { dividerClasses, dividerLabelClasses, dividerLineClasses, dividerOrientationClasses } from './variants'

const props = withDefaults(defineProps<{
  orientation?: 'horizontal' | 'vertical'
  /** subtle: between rows. strong: between groups. */
  emphasis?: 'subtle' | 'strong'
  /** Optional centred label, e.g. "or" */
  label?: string
  class?: HTMLAttributes['class']
}>(), {
  orientation: 'horizontal',
  emphasis: 'subtle',
})
</script>

<template>
  <div
    data-slot="divider"
    :role="label ? undefined : 'separator'"
    :aria-orientation="label ? undefined : orientation"
    :class="cn(dividerClasses, dividerOrientationClasses[orientation], props.class)"
  >
    <!-- With a label the lines are decoration and the label is plain text, so "or" is read out -->
    <span :aria-hidden="label ? 'true' : undefined" :class="cn(dividerLineClasses(orientation, emphasis))" />
    <template v-if="label">
      <span :class="dividerLabelClasses">{{ label }}</span>
      <span aria-hidden="true" :class="cn(dividerLineClasses(orientation, emphasis))" />
    </template>
  </div>
</template>
