<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { inject, ref, useAttrs } from 'vue'
import { useField, useFieldId } from '@/components/ui/field'
import { cn } from '@/lib/utils'
import { inputGroupInputClasses, inputGroupKey } from '.'

// The borderless input inside an InputGroup; the group draws the field.
// Extra attributes (id, type, placeholder, aria-label…) go to the native input.
defineOptions({ inheritAttrs: false })

const props = defineProps<{ class?: HTMLAttributes['class'] }>()

const model = defineModel<string>({ default: '' })
const group = inject(inputGroupKey, null)
const field = useField(() => group?.invalid.value)
const attrs = useAttrs()
// Inside a Field without `for`, the control takes the field's generated id.
const controlId = useFieldId(() => attrs.id as string | undefined)
const inputRef = ref<HTMLInputElement>()

defineExpose({ focus: () => inputRef.value?.focus() })
</script>

<template>
  <input
    ref="inputRef"
    v-model="model"
    data-slot="input-group-control"
    v-bind="$attrs"
    :id="controlId"
    :disabled="group?.disabled.value || undefined"
    :readonly="group?.readonly.value || undefined"
    :aria-invalid="field.invalid.value || undefined"
    :aria-describedby="field.describedBy.value"
    :class="cn(inputGroupInputClasses, props.class)"
  >
</template>
