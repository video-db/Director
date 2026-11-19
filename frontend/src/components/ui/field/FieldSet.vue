<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { useId } from 'vue'
import { cn } from '@/lib/utils'
import { fieldSetClass, fieldSetDescriptionClass, fieldSetLegendClass } from './variants'

// A fieldset around related fields: screen readers read the legend with each field inside it.
const props = defineProps<{
  legend: string
  /** Text under the legend, linked to the set with aria-describedby */
  description?: string
  class?: HTMLAttributes['class']
}>()
const descriptionId = `${useId()}-description`
</script>

<template>
  <fieldset data-slot="field-set" :aria-describedby="description ? descriptionId : undefined" :class="cn(fieldSetClass, props.class)">
    <legend :class="fieldSetLegendClass">
      {{ legend }}
    </legend>
    <p v-if="description" :id="descriptionId" :class="fieldSetDescriptionClass">
      {{ description }}
    </p>
    <slot />
  </fieldset>
</template>
