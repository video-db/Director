<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import type { ButtonVariants } from '.'
import { Primitive } from 'reka-ui'
import { computed } from 'vue'
import { Icon } from '@/components/ui/icon'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import { buttonIconSize, buttonSpinnerSize, buttonVariants } from '.'

interface Props extends PrimitiveProps {
  hierarchy?: ButtonVariants['hierarchy']
  destructive?: boolean
  size?: ButtonVariants['size']
  /** Material Symbols name */
  icon?: string
  /** Which side the icon, and the loading spinner, sits on */
  iconPosition?: 'leading' | 'trailing'
  loading?: boolean
  disabled?: boolean
  class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
  as: 'button',
  iconPosition: 'leading',
})

const iconSize = computed(() => buttonIconSize[props.size ?? 'md'])
const spinnerSize = computed(() => buttonSpinnerSize[props.size ?? 'md'])
const leading = computed(() => props.iconPosition === 'leading')

// A link can't be natively disabled, so a disabled or loading <Button as="a"> is taken out of the
// Tab order, marked aria-disabled and ignores clicks. A loading <button> is aria-disabled rather than
// disabled, so it keeps focus while the action runs (a disabled button would drop focus to the page).
const inactive = computed(() => props.disabled || props.loading)
const isNativeButton = computed(() => props.as === 'button' && !props.asChild)
// A native button is type="button", so it doesn't submit the form it sits in. A type attribute
// (e.g. type="submit") falls through to the element and replaces it.
const defaultType = computed(() => (isNativeButton.value ? 'button' : undefined))
function blockClick(e: MouseEvent) {
  if (inactive.value && (props.loading || !isNativeButton.value)) {
    e.preventDefault()
    e.stopImmediatePropagation()
  }
}
</script>

<template>
  <Primitive
    data-slot="button"
    :as="as"
    :as-child="asChild"
    :type="defaultType"
    :disabled="isNativeButton ? disabled : undefined"
    :aria-disabled="(!isNativeButton && inactive) || (isNativeButton && loading && !disabled) ? 'true' : undefined"
    :tabindex="!isNativeButton && inactive ? -1 : undefined"
    :aria-busy="loading || undefined"
    :class="cn(buttonVariants({ hierarchy, destructive, size }), props.class)"
    @click.capture="blockClick"
  >
    <Spinner v-if="loading && leading" :size="spinnerSize" colour="current" decorative />
    <Icon v-else-if="icon && leading" :name="icon" :size="iconSize" />
    <slot />
    <Spinner v-if="loading && !leading" :size="spinnerSize" colour="current" decorative />
    <Icon v-else-if="icon && !leading" :name="icon" :size="iconSize" />
    <span v-if="loading" class="sr-only">, loading</span>
  </Primitive>
</template>
