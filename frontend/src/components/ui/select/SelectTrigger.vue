<script setup lang="ts">
import type { SelectTriggerProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { computed, useAttrs } from 'vue'
import { SelectIcon, SelectTrigger, useForwardProps } from 'reka-ui'
import { useField, useFieldId } from '@/components/ui/field'
import { Icon } from '@/components/ui/icon'
import { inputIconSize } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { selectChevronClasses, selectLeadingIconClasses, selectTriggerVariants, selectValueWrapperClasses } from '.'

defineOptions({ inheritAttrs: false })

const props = defineProps<SelectTriggerProps & {
  /** Same heights as Button and Input: 36 / 40 / 44px */
  size?: 'sm' | 'md' | 'lg'
  invalid?: boolean
  /** Material Symbols name shown before the value */
  leadingIcon?: string
  class?: HTMLAttributes['class']
}>()

const iconSize = computed(() => inputIconSize[props.size ?? 'lg'])

const field = useField(() => props.invalid)
// Inside a Field without its own id, take the field's id so the label points here.
const attrs = useAttrs()
const triggerId = useFieldId(() => attrs.id as string | undefined)

const delegated = reactiveOmit(props, 'class', 'size', 'invalid', 'leadingIcon')
const forwarded = useForwardProps(delegated)
</script>

<template>
  <SelectTrigger
    data-slot="select-trigger"
    v-bind="{ ...forwarded, ...$attrs }"
    :id="triggerId"
    :aria-invalid="field.invalid.value || undefined"
    :aria-describedby="field.describedBy.value"
    :class="cn(selectTriggerVariants({ size }), props.class)"
  >
    <Icon v-if="leadingIcon" :name="leadingIcon" :size="iconSize" :class="selectLeadingIconClasses" />
    <span :class="selectValueWrapperClasses">
      <slot />
    </span>
    <SelectIcon as-child>
      <Icon
        name="keyboard_arrow_down"
        :size="iconSize"
        :class="selectChevronClasses"
      />
    </SelectIcon>
  </SelectTrigger>
</template>
