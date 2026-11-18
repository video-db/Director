<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, inject, onMounted, useAttrs, useSlots } from 'vue'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { inputGroupButtonClasses, inputGroupKey } from '.'

// A compact Button that fits inside the field: 28px in a sm group, 32px in md and lg.
// With no label text it is a square icon button, named by `label`.
const props = withDefaults(defineProps<{
  hierarchy?: 'primary' | 'secondary' | 'tertiary'
  /** xs: 28px. sm: 32px. Defaults to fit the group. */
  size?: 'xs' | 'sm'
  /** Material Symbols name (16px) */
  icon?: string
  iconPosition?: 'leading' | 'trailing'
  /** Accessible name. Required when the button shows only an icon. */
  label?: string
  type?: 'button' | 'submit' | 'reset'
  loading?: boolean
  disabled?: boolean
  class?: HTMLAttributes['class']
}>(), {
  hierarchy: 'tertiary',
  iconPosition: 'leading',
  type: 'button',
})

const slots = useSlots()
const attrs = useAttrs()
const group = inject(inputGroupKey, null)
const resolvedSize = computed(() => props.size ?? (group?.size.value === 'sm' ? 'xs' : 'sm'))
// Called from the template so it is checked on every render: slots aren't reactive, so a computed would keep its first answer.
const isIconOnly = () => !slots.default

if (import.meta.env.DEV) {
  onMounted(() => {
    if (isIconOnly() && !props.label && !attrs['aria-label'] && !attrs['aria-labelledby'])
      console.warn('[InputGroupButton] An icon-only button needs `label` (or aria-label) so screen readers can name it.')
  })
}
</script>

<template>
  <!-- Button size sm gives the 16px icon and Text sm; inputGroupButtonClasses set the height and padding. -->
  <Button
    data-slot="input-group-button"
    :type="type"
    :hierarchy="hierarchy"
    size="sm"
    :icon="icon"
    :icon-position="iconPosition"
    :loading="loading"
    :disabled="disabled || group?.disabled.value"
    :aria-label="isIconOnly() ? label : undefined"
    :class="cn(inputGroupButtonClasses(resolvedSize, isIconOnly()), props.class)"
  >
    <slot v-if="!isIconOnly()" />
  </Button>
</template>
