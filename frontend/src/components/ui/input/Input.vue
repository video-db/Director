<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { InputVariants } from '.'
import { computed, ref, useAttrs } from 'vue'
import { useField, useFieldId } from '@/components/ui/field'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { inputClearButtonClass, inputControlClass, inputIconSize, inputLeadingIconClass, inputTrailingIconClass, inputVariants } from './variants'

defineOptions({ inheritAttrs: false })

const props = defineProps<{
  size?: InputVariants['size']
  /** Material Symbols name shown before the text, e.g. "search" or "link" */
  leadingIcon?: string
  /** Material Symbols name shown after the text */
  trailingIcon?: string
  /** Show a clear (×) button while the field has a value */
  clearable?: boolean
  invalid?: boolean
  disabled?: boolean
  readonly?: boolean
  class?: HTMLAttributes['class']
}>()

const model = defineModel<string>({ default: '' })
const field = useField(() => props.invalid)
const attrs = useAttrs()
// Inside a Field without `for`, the input takes the field's generated id.
const inputId = useFieldId(() => attrs.id as string | undefined)
const inputRef = ref<HTMLInputElement>()

const iconSize = computed(() => inputIconSize[props.size ?? 'lg'])
const leadingIconClass = computed(() => inputLeadingIconClass({ disabled: props.disabled, invalid: field.invalid.value, filled: !!model.value }))

function clear() {
  model.value = ''
  inputRef.value?.focus()
}

defineExpose({ focus: () => inputRef.value?.focus() })
</script>

<template>
  <div
    data-slot="input"
    :data-invalid="field.invalid.value ? '' : undefined"
    :data-disabled="disabled ? '' : undefined"
    :data-readonly="props.readonly ? '' : undefined"
    :class="cn(inputVariants({ size }), props.class)"
  >
    <Icon v-if="leadingIcon" :name="leadingIcon" :size="iconSize" :class="leadingIconClass" />
    <input
      ref="inputRef"
      v-model="model"
      data-slot="input-control"
      v-bind="$attrs"
      :id="inputId"
      :disabled="disabled"
      :readonly="props.readonly"
      :aria-invalid="field.invalid.value || undefined"
      :aria-describedby="field.describedBy.value"
      :class="inputControlClass"
    >
    <button
      v-if="clearable && model && !disabled && !props.readonly"
      type="button"
      aria-label="Clear"
      :class="inputClearButtonClass"
      @click="clear"
    >
      <Icon name="close" :size="iconSize" />
    </button>
    <Icon
      v-else-if="trailingIcon"
      :name="trailingIcon"
      :size="iconSize"
      :class="inputTrailingIconClass(disabled)"
    />
  </div>
</template>
