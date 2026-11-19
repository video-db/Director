<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from '@/lib/utils'
import { formatDuration, formatIsoDuration, parseDuration } from './format'
import { durationLabelClasses, durationLabelEmphases, durationLabelSizes } from './variants'

const props = withDefaults(defineProps<{
  /** Seconds (formatted as mm:ss or h:mm:ss) or a ready-made string */
  value: number | string
  /** scrim: half-opaque black for use on media. solid: opaque black. */
  emphasis?: 'scrim' | 'solid'
  size?: 'sm' | 'md'
  class?: HTMLAttributes['class']
}>(), {
  emphasis: 'scrim',
  size: 'sm',
})

const text = computed(() => (typeof props.value === 'number' ? formatDuration(props.value) : props.value))
// Machine-readable length, e.g. "PT1M15S". Strings that aren't a time, such as "LIVE", get none.
const seconds = computed(() => (typeof props.value === 'number' ? props.value : parseDuration(props.value)))
const datetime = computed(() => (seconds.value === undefined ? undefined : formatIsoDuration(seconds.value)))
</script>

<template>
  <span
    data-slot="duration-label"
    :class="cn(durationLabelClasses, durationLabelEmphases[emphasis], durationLabelSizes[size], props.class)"
  >
    <time v-if="datetime" :datetime="datetime">{{ text }}</time>
    <template v-else>{{ text }}</template>
  </span>
</template>
