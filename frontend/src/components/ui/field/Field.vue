<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, provide, useId } from 'vue'
import { cn } from '@/lib/utils'
import { fieldKey } from './context'
import type { FieldOrientation } from './variants'
import {
  fieldControlHorizontalClass,
  fieldControlHorizontalTallClass,
  fieldDescriptionClass,
  fieldLabelClass,
  fieldLabelRowClass,
  fieldMessageClass,
  fieldMessageHorizontalClass,
  fieldOrientations,
  fieldRequiredClass,
} from './variants'

const props = withDefaults(defineProps<{
  label: string
  /** id of the control, so the label is linked to it. Generated when left out. The label's own id is this plus "-label". */
  for?: string
  /** Text between the label and the control, e.g. a password rule */
  description?: string
  /** vertical: label above the control. horizontal: label left, control right, e.g. a Switch. */
  orientation?: FieldOrientation
  /** Helper text under the control */
  helper?: string
  /** Error message. Replaces the helper text, and turns it and the label red. */
  error?: string
  /** Adds a red asterisk to the label; screen readers hear "(required)". Set required on the control too. */
  required?: boolean
  disabled?: boolean
  class?: HTMLAttributes['class']
}>(), {
  orientation: 'vertical',
})

// Without `for`, the field generates an id and hands it to the first control inside that has no id
// of its own (Input, Textarea, Select's trigger, Combobox's input, Chip Input, Input Group's control,
// Checkbox, Switch).
const generatedId = useId()
const controlId = computed(() => props.for ?? generatedId)
let claimed = false

// Input, Textarea, Select, Combobox, Chip Input, Input Group, Radio Group, Slider, Checkbox and Switch
// inside pick these up: the message is linked with aria-describedby, and an error marks the control invalid.
const descriptionId = computed(() => (props.description ? `${controlId.value}-description` : undefined))
const messageId = computed(() => (props.error || props.helper ? `${controlId.value}-message` : undefined))
const horizontal = computed(() => props.orientation === 'horizontal')
provide(fieldKey, {
  // The description and the message, both read after the label
  messageId: computed(() => [descriptionId.value, messageId.value].filter(Boolean).join(' ') || undefined),
  invalid: computed(() => !!props.error),
  controlId,
  claimControlId: () => {
    if (props.for || claimed) return undefined
    claimed = true
    return generatedId
  },
  releaseControlId: () => {
    claimed = false
  },
})
</script>

<template>
  <div data-slot="field" :data-orientation="orientation" :class="cn(fieldOrientations[orientation], props.class)">
    <!-- The label row: the trailing slot sits at its end, e.g. a Badge -->
    <div :class="fieldLabelRowClass">
      <label
        :id="`${controlId}-label`"
        :for="controlId"
        :class="fieldLabelClass(disabled, !!error)"
      >
        {{ label }}<template v-if="required">
          <span aria-hidden="true" :class="fieldRequiredClass(disabled)">*</span>
          <span class="sr-only">(required)</span>
        </template>
      </label>
      <slot name="trailing" />
    </div>
    <p v-if="description" :id="descriptionId" :class="fieldDescriptionClass">
      {{ description }}
    </p>
    <div v-if="horizontal" :class="[fieldControlHorizontalClass, description && fieldControlHorizontalTallClass]">
      <slot />
    </div>
    <slot v-else />
    <!-- Always in the DOM (visually hidden while empty), so the alert inside is already live when an
         error appears and screen readers announce it. Only the error is in the alert, not the helper. -->
    <p
      :id="messageId"
      :class="[fieldMessageClass(error, helper), horizontal && fieldMessageHorizontalClass]"
    >
      <span role="alert">{{ error }}</span>
      <template v-if="!error">
        {{ helper }}
      </template>
    </p>
  </div>
</template>
