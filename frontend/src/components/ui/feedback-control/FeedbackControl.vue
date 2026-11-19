<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { IconButton } from '@/components/ui/icon-button'
import { cn } from '@/lib/utils'
import { feedbackControlButtonClasses, feedbackControlClasses } from '.'

// Click again to clear.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()

const model = defineModel<'liked' | 'disliked' | null>({ default: null })

// Not helpful first, then helpful, as in the console.
const options = [
  { value: 'disliked', icon: 'thumb_down', label: 'Mark response as not helpful' },
  { value: 'liked', icon: 'thumb_up', label: 'Mark response as helpful' },
] as const

function toggle(v: 'liked' | 'disliked') {
  model.value = model.value === v ? null : v
}
</script>

<template>
  <div data-slot="feedback-control" role="group" aria-label="Rate this response" :class="cn(feedbackControlClasses, props.class)">
    <IconButton
      v-for="o in options"
      :key="o.value"
      :icon="o.icon"
      :label="o.label"
      :pressed="model === o.value"
      size="xs"
      :class="feedbackControlButtonClasses"
      @click="toggle(o.value)"
    />
  </div>
</template>
