<script setup lang="ts">
import type { SelectRootEmits, SelectRootProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import { injectSelectRootContext, SelectRoot, useForwardPropsEmits, VisuallyHidden } from 'reka-ui'
import { computed, defineComponent, h } from 'vue'

const props = defineProps<SelectRootProps>()
const emits = defineEmits<SelectRootEmits>()
// With multiple, Reka's hidden <select multiple> gets the values joined ("a,b") and submits nothing,
// so it doesn't get the name: a hidden input per value submits them instead (name=a&name=b), as in React.
const delegated = reactiveOmit(props, 'name')
const forwarded = useForwardPropsEmits(delegated, emits)
const rootName = computed(() => (props.multiple ? undefined : props.name))

// The values of a multiple select, for the form. While required and empty, a hidden required input stops
// the form submitting; the browser focuses it, and it hands focus to the trigger.
const MultipleFormValues = defineComponent({
  props: { name: { type: String, required: true }, values: { type: Array, required: true }, required: Boolean, disabled: Boolean },
  setup(p) {
    const root = injectSelectRootContext()
    return () => [
      ...(p.values as unknown[]).map(value => h('input', { key: String(value), type: 'hidden', name: p.name, value: String(value), disabled: p.disabled || undefined })),
      p.required && !p.values.length
        ? h(VisuallyHidden, { 'as': 'input', 'aria-hidden': 'true', 'tabindex': -1, 'required': true, 'disabled': p.disabled || undefined, 'value': '', 'onFocus': () => root.triggerElement.value?.focus() })
        : null,
    ]
  },
})
</script>

<template>
  <SelectRoot v-slot="{ modelValue }" data-slot="select" v-bind="forwarded" :name="rootName">
    <slot />
    <MultipleFormValues
      v-if="multiple && name"
      :name="name"
      :values="Array.isArray(modelValue) ? modelValue : []"
      :required="required"
      :disabled="disabled"
    />
  </SelectRoot>
</template>
