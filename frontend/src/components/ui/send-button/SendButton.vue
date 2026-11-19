<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { Icon } from '@/components/ui/icon'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import { isOwnPress, sendButtonIconSize, sendButtonSpinnerSize, sendButtonState, sendButtonVariants } from './variants'

// idle (nothing to send yet) → active (ready) → processing (sent, waiting) ; or disabled. With stoppable, it is a
// Stop button while processing: pressing it fires stop instead of submitting.
const props = withDefaults(defineProps<{
  /** There is something to send: turns the button brand orange */
  ready?: boolean
  /** Sent and waiting for a reply */
  processing?: boolean
  /** While processing, show a Stop button that fires stop */
  stoppable?: boolean
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  label?: string
  /** Accessible label while it is a Stop button */
  stopLabel?: string
  class?: HTMLAttributes['class']
}>(), {
  size: 'md',
  label: 'Send message',
  stopLabel: 'Stop generating',
})
const emit = defineEmits<{ stop: [] }>()

const stopping = computed(() => !props.disabled && props.processing && props.stoppable)
const inactive = computed(() => props.disabled || props.processing || !props.ready)

function onClick(event: MouseEvent) {
  if (inactive.value) event.preventDefault()
  if (stopping.value && isOwnPress(event, event.currentTarget as Element)) emit('stop')
}
</script>

<template>
  <button
    data-slot="send-button"
    type="submit"
    :aria-label="stopping ? stopLabel : processing ? 'Sending' : label"
    :aria-busy="(processing && !stopping) || undefined"
    :aria-disabled="(inactive && !stopping) || undefined"
    :disabled="disabled"
    :class="cn(sendButtonVariants({ size, state: sendButtonState(props) }), props.class)"
    @click="onClick"
  >
    <Icon v-if="stopping" name="stop" filled :size="sendButtonIconSize[size]" />
    <Spinner v-else-if="processing" colour="neutral" :size="sendButtonSpinnerSize[size]" decorative />
    <Icon v-else name="arrow_upward" :size="sendButtonIconSize[size]" />
  </button>
</template>
