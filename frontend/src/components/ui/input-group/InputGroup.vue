<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { InputGroupSize } from '.'
import { computed, provide } from 'vue'
import { useField } from '@/components/ui/field'
import { inputVariants } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { inputGroupClasses, inputGroupKey, inputGroupStackedClasses } from '.'

// The Input field's look, with addons inside it: icons, text, buttons and key hints on either
// side (inline-start / inline-end), or toolbars above and below (block-start / block-end).
const props = withDefaults(defineProps<{
  size?: InputGroupSize
  invalid?: boolean
  disabled?: boolean
  readonly?: boolean
  class?: HTMLAttributes['class']
}>(), {
  size: 'lg',
})

// Inside a Field with an error, the whole group turns invalid.
const field = useField(() => props.invalid)

provide(inputGroupKey, {
  size: computed(() => props.size),
  invalid: field.invalid,
  disabled: computed(() => !!props.disabled),
  readonly: computed(() => !!props.readonly),
})
</script>

<template>
  <div
    data-slot="input-group"
    role="group"
    :data-size="size"
    :data-invalid="field.invalid.value ? '' : undefined"
    :data-disabled="disabled ? '' : undefined"
    :data-readonly="props.readonly ? '' : undefined"
    :class="cn(inputVariants({ size }), inputGroupClasses, inputGroupStackedClasses(size), props.class)"
  >
    <slot />
  </div>
</template>
