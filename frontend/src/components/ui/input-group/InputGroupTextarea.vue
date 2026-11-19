<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { inject, ref, useAttrs } from 'vue'
import { useField, useFieldId } from '@/components/ui/field'
import { cn } from '@/lib/utils'
import { inputGroupKey, inputGroupTextareaClasses } from '.'

// The borderless textarea inside an InputGroup. The group stacks around it, so put
// toolbars in block-start / block-end addons. Attributes go to the native textarea.
defineOptions({ inheritAttrs: false })

const props = defineProps<{ class?: HTMLAttributes['class'] }>()

const model = defineModel<string>({ default: '' })
const group = inject(inputGroupKey, null)
const field = useField(() => group?.invalid.value)
const attrs = useAttrs()
// Inside a Field without `for`, the control takes the field's generated id.
const controlId = useFieldId(() => attrs.id as string | undefined)
const textareaRef = ref<HTMLTextAreaElement>()

defineExpose({ focus: () => textareaRef.value?.focus() })
</script>

<template>
  <textarea
    ref="textareaRef"
    v-model="model"
    data-slot="input-group-control"
    v-bind="$attrs"
    :id="controlId"
    :disabled="group?.disabled.value || undefined"
    :readonly="group?.readonly.value || undefined"
    :aria-invalid="field.invalid.value || undefined"
    :aria-describedby="field.describedBy.value"
    :class="cn(inputGroupTextareaClasses, props.class)"
  />
</template>
