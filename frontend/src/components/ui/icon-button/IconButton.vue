<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { IconButtonVariants } from '.'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { iconButtonIconSize, iconButtonVariants } from '.'

const props = withDefaults(defineProps<{
  /** Material Symbols name */
  icon: string
  /** Required: icon-only buttons need an accessible name */
  label: string
  hierarchy?: IconButtonVariants['hierarchy']
  size?: IconButtonVariants['size']
  shape?: IconButtonVariants['shape']
  /** Filled icon instead of outlined, e.g. a play button */
  filled?: boolean
  /** Makes it a toggle (aria-pressed), e.g. thumbs up. Leave unset for plain actions. */
  pressed?: boolean
  disabled?: boolean
  class?: HTMLAttributes['class']
}>(), {
  pressed: undefined,
})
</script>

<template>
  <button
    data-slot="icon-button"
    type="button"
    :aria-label="label"
    :aria-pressed="pressed"
    :disabled="disabled"
    :class="cn(iconButtonVariants({ hierarchy, size, shape }), props.class)"
  >
    <!-- The slot replaces the icon, e.g. with a Spinner. -->
    <slot>
      <Icon :name="icon" :size="iconButtonIconSize[size ?? 'md']" :filled="filled || pressed" />
    </slot>
  </button>
</template>
