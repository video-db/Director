<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import type { BadgeVariants, PillVariants } from './variants'
import { Primitive } from 'reka-ui'
import { computed } from 'vue'
import { Icon } from '@/components/ui/icon'
import { Spinner } from '@/components/ui/spinner'
import { useLabelText } from '@/lib/use-label-text'
import { cn } from '@/lib/utils'
import { badgeRemoveClasses, badgeRemoveHitArea, badgeSpinnerSize, badgeVariants, pillDotClasses, pillDotSize, pillIconSize, pillVariants } from './variants'

// Render it as a link with as="a" and href (or as-child around a router link).
const props = withDefaults(defineProps<PrimitiveProps & {
  colour?: BadgeVariants['colour']
  emphasis?: BadgeVariants['emphasis']
  size?: PillVariants['size']
  /** Leading dot in the badge's colour */
  dot?: boolean
  /** Material Symbols icon */
  icon?: string
  /** Which side the icon (or the loading spinner) sits on */
  iconPosition?: 'leading' | 'trailing'
  /** A spinner in the icon's place, for work in progress such as "Deleting" */
  loading?: boolean
  /** Shows a remove (×) button and emits "remove" */
  removable?: boolean
  /** Accessible name for the remove button. Defaults to "Remove" plus the badge text. */
  removeLabel?: string
  class?: HTMLAttributes['class']
}>(), {
  as: 'span',
  iconPosition: 'leading',
})

const emit = defineEmits<{ remove: [] }>()

// Name the remove button after the badge text, e.g. "Remove Editor".
const { label: textEl, text } = useLabelText()

const s = computed(() => props.size ?? 'md')
const leading = computed(() => props.iconPosition === 'leading')
</script>

<template>
  <Primitive
    data-slot="badge"
    :as="as"
    :as-child="asChild"
    :class="cn(pillVariants({ size }), badgeVariants({ colour, emphasis }), removable && 'pr-4', props.class)"
  >
    <span v-if="dot" aria-hidden="true" :class="[pillDotClasses, pillDotSize[s]]" />
    <Spinner v-else-if="loading && leading" :size="badgeSpinnerSize[s]" colour="current" decorative />
    <Icon v-else-if="icon && leading" :name="icon" :size="pillIconSize[s]" />
    <span ref="textEl" class="contents"><slot /></span>
    <Spinner v-if="loading && !leading" :size="badgeSpinnerSize[s]" colour="current" decorative />
    <Icon v-else-if="icon && !leading" :name="icon" :size="pillIconSize[s]" />
    <button
      v-if="removable"
      type="button"
      :aria-label="removeLabel ?? (text ? `Remove ${text}` : 'Remove')"
      :class="[badgeRemoveClasses, badgeRemoveHitArea[s]]"
      @click="emit('remove')"
    >
      <Icon name="close" :size="pillIconSize[s]" />
    </button>
  </Primitive>
</template>
