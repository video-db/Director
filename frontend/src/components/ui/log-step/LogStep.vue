<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { CollapsibleRoot } from 'reka-ui'
import { computed, useId } from 'vue'
import { CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Icon } from '@/components/ui/icon'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import { logStepChevronClasses, logStepClasses, logStepDetailClasses, logStepLabelClasses, logStepRowClasses, logStepRowExpandableClasses, logStepStatusClasses, logStepStatusIconClasses } from './variants'

// One step in Director's log; expands to show detail.
const props = withDefaults(defineProps<{
  label: string
  status?: 'running' | 'done' | 'failed'
  /** Detail text. Or use the default slot. Without either, the step is a plain row, not a button. */
  detail?: string
  class?: HTMLAttributes['class']
}>(), {
  status: 'done',
})

const open = defineModel<boolean>('open', { default: false })
const statusId = useId()
// Always rendered, so screen readers announce it when the status changes
const statusText = computed(() => `${props.label} ${props.status}`)
</script>

<template>
  <CollapsibleRoot
    v-model:open="open"
    data-slot="log-step"
    :class="cn(logStepClasses, props.class)"
  >
    <span :id="statusId" role="status" class="sr-only">{{ statusText }}</span>
    <!-- $slots is read in the template rather than a computed, so it stays up to date. The library's
         trigger gives the detail its id up front, so aria-controls points at it from the start; the row
         is the trigger itself, without Collapsible's data-slot. -->
    <component
      :is="detail || $slots.default ? CollapsibleTrigger : 'div'"
      :data-slot="undefined"
      :aria-describedby="detail || $slots.default ? statusId : undefined"
      :class="detail || $slots.default ? cn(logStepRowClasses, logStepRowExpandableClasses) : logStepRowClasses"
    >
      <!-- Decorative: the status region says the same in words -->
      <span aria-hidden="true" :class="logStepStatusClasses">
        <Spinner v-if="status === 'running'" size="sm" decorative />
        <Icon v-else :name="status === 'done' ? 'check_circle' : 'error'" :class="logStepStatusIconClasses[status]" />
      </span>
      <span :class="logStepLabelClasses" :aria-hidden="detail || $slots.default ? undefined : 'true'">{{ label }}</span>
      <Icon
        v-if="detail || $slots.default"
        name="keyboard_arrow_down"
        :class="logStepChevronClasses"
      />
    </component>
    <CollapsibleContent v-if="detail || $slots.default">
      <div :class="logStepDetailClasses">
        <slot>{{ detail }}</slot>
      </div>
    </CollapsibleContent>
  </CollapsibleRoot>
</template>
