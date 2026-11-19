<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { SegmentedControlOption } from '.'
import { ToggleGroupItem, ToggleGroupRoot } from 'reka-ui'
import { onMounted, useAttrs } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { segmentedControlClasses, segmentedControlIconSize, segmentedControlItemClasses } from '.'

const props = withDefaults(defineProps<{
  options: SegmentedControlOption[]
  /** md: 40px, as in the sidebar and the Media Library toolbar. sm: 36px for tighter spaces. */
  size?: 'sm' | 'md'
  /** Accessible name for the group. Or pass aria-label / aria-labelledby. */
  label?: string
  disabled?: boolean
  class?: HTMLAttributes['class']
}>(), {
  size: 'md',
})

const model = defineModel<string>({ required: true })
const attrs = useAttrs()

if (import.meta.env.DEV) {
  onMounted(() => {
    if (!props.label && !attrs['aria-label'] && !attrs['aria-labelledby'])
      console.warn('[SegmentedControl] The group has no accessible name: pass `label`, aria-label or aria-labelledby.')
  })
}

// A segmented control always has one option selected, so ignore attempts to deselect.
function select(value: unknown) {
  if (typeof value === 'string' && value) model.value = value
}
</script>

<template>
  <ToggleGroupRoot
    data-slot="segmented-control"
    type="single"
    :model-value="model"
    :disabled="disabled"
    :aria-label="label"
    :class="cn(segmentedControlClasses(size), props.class)"
    @update:model-value="select"
  >
    <ToggleGroupItem
      v-for="o in options"
      :key="o.value"
      :value="o.value"
      :disabled="o.disabled"
      :class="cn(segmentedControlItemClasses(size))"
    >
      <Icon v-if="o.icon" :name="o.icon" :size="segmentedControlIconSize" />
      {{ o.label }}
    </ToggleGroupItem>
  </ToggleGroupRoot>
</template>
