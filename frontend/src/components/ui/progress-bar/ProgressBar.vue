<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, useId } from 'vue'
import { cn } from '@/lib/utils'
import { progressBarClasses, progressBarFillClasses, progressBarFills, progressBarLabelClasses, progressBarLabelledClasses, progressBarLabelRowClasses, progressBarLabelValueClasses, progressBarPercent, progressBarTrackClasses, progressBarTrackSizes, progressBarValueClasses } from './variants'

const props = withDefaults(defineProps<{
  /** 0 to 100 */
  value: number
  size?: 'sm' | 'md'
  colour?: 'brand' | 'success' | 'error'
  /** Show the percentage after the bar (with showLabel, at the end of the label row) */
  showValue?: boolean
  /** Accessible label, e.g. "Uploading video.mp4" */
  label?: string
  /** Show the label above the bar; it then names the bar */
  showLabel?: boolean
  class?: HTMLAttributes['class']
}>(), {
  size: 'md',
  colour: 'brand',
  label: 'Progress',
})

const pct = computed(() => progressBarPercent(props.value))
const labelId = useId()
</script>

<template>
  <div data-slot="progress-bar" :class="cn(showLabel ? progressBarLabelledClasses : progressBarClasses, props.class)">
    <div v-if="showLabel" :class="progressBarLabelRowClasses">
      <span :id="labelId" :class="progressBarLabelClasses">{{ label }}</span>
      <span v-if="showValue" :class="progressBarLabelValueClasses">{{ pct }}%</span>
    </div>
    <div
      role="progressbar"
      :aria-label="showLabel ? undefined : label"
      :aria-labelledby="showLabel ? labelId : undefined"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-valuenow="pct"
      :class="cn(progressBarTrackClasses, progressBarTrackSizes[size], showLabel && 'w-full flex-none')"
    >
      <div :class="cn(progressBarFillClasses, progressBarFills[colour])" :style="{ width: `${pct}%` }" />
    </div>
    <span v-if="showValue && !showLabel" :class="progressBarValueClasses">{{ pct }}%</span>
  </div>
</template>
