<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { TextareaVariants } from './variants'
import { useAttrs } from 'vue'
import { useField, useFieldId } from '@/components/ui/field'
import { cn } from '@/lib/utils'
import { textareaVariants } from './variants'

defineOptions({ inheritAttrs: false })

const props = defineProps<{
  size?: TextareaVariants['size']
  invalid?: boolean
  disabled?: boolean
  readonly?: boolean
  class?: HTMLAttributes['class']
}>()

const model = defineModel<string>({ default: '' })
const field = useField(() => props.invalid)
const attrs = useAttrs()
// Inside a Field without `for`, the textarea takes the field's generated id.
const textareaId = useFieldId(() => attrs.id as string | undefined)
</script>

<template>
  <textarea
    v-model="model"
    data-slot="textarea"
    v-bind="$attrs"
    :id="textareaId"
    :disabled="disabled"
    :readonly="props.readonly"
    :data-readonly="props.readonly ? '' : undefined"
    :aria-invalid="field.invalid.value || undefined"
    :aria-describedby="field.describedBy.value"
    :class="cn(textareaVariants({ size }), props.class)"
  />
</template>
