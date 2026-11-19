<script setup lang="ts">
import type { DropdownMenuRadioItemEmits, DropdownMenuRadioItemProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuItemIndicator, DropdownMenuRadioItem, useForwardPropsEmits } from 'reka-ui'
import { Icon } from '@/components/ui/icon'
import { useLabelText } from '@/lib/use-label-text'
import { cn } from '@/lib/utils'
import { listItemIconClasses } from '@/lib/floating'
import { menuItemCheckClasses, menuItemClasses, menuItemIndicatorClasses, menuItemLabelClasses } from '.'

// A menu item with a trailing check for the selected option.
const props = defineProps<DropdownMenuRadioItemProps & {
  icon?: string
  class?: HTMLAttributes['class']
}>()
const emits = defineEmits<DropdownMenuRadioItemEmits>()
const delegated = reactiveOmit(props, 'class', 'icon', 'textValue')
const forwarded = useForwardPropsEmits(delegated, emits)
// Typeahead matches the label only, not the icon's ligature name.
const { label, text } = useLabelText()
</script>

<template>
  <DropdownMenuRadioItem
    data-slot="dropdown-menu-radio-item"
    v-bind="forwarded"
    :text-value="textValue ?? text"
    :class="cn(menuItemClasses, props.class)"
  >
    <Icon v-if="icon" :name="icon" :class="listItemIconClasses" />
    <span ref="label" :class="menuItemLabelClasses"><slot /></span>
    <DropdownMenuItemIndicator :class="menuItemIndicatorClasses">
      <Icon name="check" :class="menuItemCheckClasses" />
    </DropdownMenuItemIndicator>
  </DropdownMenuRadioItem>
</template>
