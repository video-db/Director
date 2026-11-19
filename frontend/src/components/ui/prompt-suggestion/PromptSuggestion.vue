<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { promptSuggestionClasses, promptSuggestionIconClasses, promptSuggestionLabelClasses } from './variants'

// A row in a list of suggested prompts.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <button
    data-slot="prompt-suggestion"
    type="button"
    :class="cn(promptSuggestionClasses, props.class)"
  >
    <Icon name="arrow_forward" :class="promptSuggestionIconClasses" />
    <span :class="promptSuggestionLabelClasses"><slot /></span>
  </button>
</template>
