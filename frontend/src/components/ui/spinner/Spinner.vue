<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { SpinnerColour, SpinnerSize } from './variants'
import { cn } from '@/lib/utils'
import { spinnerDashArray, spinnerRadius, spinnerSizes, spinnerStrokeWidth, spinnerTones } from './variants'

const props = withDefaults(defineProps<{
  size?: SpinnerSize
  /** current takes the text colour, e.g. inside a Button */
  colour?: SpinnerColour
  /** Read out by screen readers */
  label?: string
  /** Hide it from screen readers, e.g. inside a button that already says "Sending" */
  decorative?: boolean
  class?: HTMLAttributes['class']
}>(), {
  size: 'md',
  colour: 'brand',
  label: 'Loading',
})
</script>

<template>
  <!-- The label is real text in a status region, which screen readers announce more reliably than aria-label -->
  <span
    data-slot="spinner"
    :role="decorative ? undefined : 'status'"
    :aria-hidden="decorative || undefined"
    :class="cn('inline-flex shrink-0', props.class)"
  >
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      :width="spinnerSizes[size]"
      :height="spinnerSizes[size]"
      class="animate-spin"
    >
      <circle cx="12" cy="12" :r="spinnerRadius" :stroke-width="spinnerStrokeWidth" :class="spinnerTones[colour][0]" />
      <circle
        cx="12"
        cy="12"
        :r="spinnerRadius"
        :stroke-width="spinnerStrokeWidth"
        :stroke-dasharray="spinnerDashArray"
        transform="rotate(-90 12 12)"
        :class="spinnerTones[colour][1]"
      />
    </svg>
    <span v-if="!decorative" class="sr-only">{{ label }}</span>
  </span>
</template>
