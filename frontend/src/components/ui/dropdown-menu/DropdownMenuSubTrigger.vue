<script setup lang="ts">
import type { DropdownMenuSubTriggerProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuSubTrigger, useForwardProps } from 'reka-ui'
import { Icon } from '@/components/ui/icon'
import { useLabelText } from '@/lib/use-label-text'
import { cn } from '@/lib/utils'
import { listItemIconClasses } from '@/lib/floating'
import { menuItemClasses, menuItemLabelClasses, menuSubTriggerChevronClasses, menuSubTriggerClasses } from '.'

// A menu item with a trailing chevron that opens a submenu.
const props = defineProps<DropdownMenuSubTriggerProps & {
  icon?: string
  class?: HTMLAttributes['class']
}>()
const delegated = reactiveOmit(props, 'class', 'icon', 'textValue')
const forwarded = useForwardProps(delegated)
// Typeahead matches the label only, not the icon's ligature name.
const { label, text } = useLabelText()
</script>

<template>
  <DropdownMenuSubTrigger
    data-slot="dropdown-menu-sub-trigger"
    v-bind="forwarded"
    :text-value="textValue ?? text"
    :class="cn(menuItemClasses, menuSubTriggerClasses, props.class)"
  >
    <Icon v-if="icon" :name="icon" :class="listItemIconClasses" />
    <span ref="label" :class="menuItemLabelClasses"><slot /></span>
    <Icon name="chevron_right" :class="menuSubTriggerChevronClasses" />
  </DropdownMenuSubTrigger>
</template>
