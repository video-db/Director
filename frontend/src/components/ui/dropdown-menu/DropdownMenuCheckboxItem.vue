<script setup lang="ts">
import type { DropdownMenuCheckboxItemEmits, DropdownMenuCheckboxItemProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuCheckboxItem, DropdownMenuItemIndicator, useForwardPropsEmits } from 'reka-ui'
import { listItemClasses, listItemIconClasses } from '@/lib/floating'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { useLabelText } from '@/lib/use-label-text'
import { menuItemCheckClasses, menuItemIndicatorClasses, menuItemLabelClasses } from '.'

// An on/off item (v-model) with a trailing check, like the radio item. Selecting it closes the
// menu; call preventDefault() in @select to keep the menu open for more changes.
const props = defineProps<DropdownMenuCheckboxItemProps & {
  icon?: string
  class?: HTMLAttributes['class']
}>()
const emits = defineEmits<DropdownMenuCheckboxItemEmits>()
const delegated = reactiveOmit(props, 'class', 'icon', 'textValue')
const forwarded = useForwardPropsEmits(delegated, emits)
const { label, text } = useLabelText()
</script>

<template>
  <DropdownMenuCheckboxItem
    data-slot="dropdown-menu-checkbox-item"
    v-bind="forwarded"
    :text-value="textValue ?? text"
    :class="cn(listItemClasses, props.class)"
  >
    <Icon v-if="icon" :name="icon" :class="listItemIconClasses" />
    <span ref="label" :class="menuItemLabelClasses"><slot /></span>
    <DropdownMenuItemIndicator :class="menuItemIndicatorClasses">
      <Icon name="check" :class="menuItemCheckClasses" />
    </DropdownMenuItemIndicator>
  </DropdownMenuCheckboxItem>
</template>
