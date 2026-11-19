<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { AlertTone } from '.'
import { computed } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { alertActionClasses, alertClasses, alertMessageClasses, alertStyles } from '.'

// Put a message in the default slot, or an AlertTitle and AlertDescription; put an action in the #action slot.
const props = withDefaults(defineProps<{
  status?: AlertTone
  /** A Material Symbols name in place of the status's icon. A neutral alert has none unless you set one. */
  icon?: string
  /**
   * Set when the alert appears in response to something (a failed save, a finished upload) so
   * screen readers announce it: role="alert" for warning, error and destructive, role="status" otherwise.
   * Leave off for banners that are part of the page, which would otherwise be read on every load.
   */
  live?: boolean
  class?: HTMLAttributes['class']
}>(), {
  status: 'info',
  live: false,
})

const style = computed(() => alertStyles[props.status])
const glyph = computed(() => props.icon ?? style.value.glyph)
const urgent = computed(() => ['error', 'warning', 'destructive'].includes(props.status))
</script>

<template>
  <div
    data-slot="alert"
    :data-status="status"
    :role="live ? (urgent ? 'alert' : 'status') : undefined"
    :class="cn(alertClasses, style.box, props.class)"
  >
    <Icon v-if="glyph" :name="glyph" :class="style.icon" />
    <div :class="alertMessageClasses">
      <slot />
    </div>
    <div v-if="$slots.action" :class="alertActionClasses">
      <slot name="action" />
    </div>
  </div>
</template>
