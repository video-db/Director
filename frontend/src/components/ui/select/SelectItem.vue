<script setup lang="ts">
import type { SelectItemProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { SelectItem, SelectItemIndicator, SelectItemText, useForwardProps } from 'reka-ui'
import { Icon } from '@/components/ui/icon'
import { listItemClasses, listItemIconClasses } from '@/lib/floating'
import { cn } from '@/lib/utils'
import { selectItemCheckClasses, selectItemIndicatorClasses, selectItemTextClasses } from '.'

const props = defineProps<SelectItemProps & {
  /** Material Symbols name shown before the label */
  icon?: string
  class?: HTMLAttributes['class']
}>()

const delegated = reactiveOmit(props, 'class', 'icon')
const forwarded = useForwardProps(delegated)
</script>

<template>
  <SelectItem
    data-slot="select-item"
    v-bind="forwarded"
    :class="cn(
      listItemClasses,
      props.class,
    )"
  >
    <Icon v-if="icon" :name="icon" :class="listItemIconClasses" />
    <SelectItemText :class="selectItemTextClasses">
      <slot />
    </SelectItemText>
    <SelectItemIndicator :class="selectItemIndicatorClasses">
      <Icon name="check" :class="selectItemCheckClasses" />
    </SelectItemIndicator>
  </SelectItem>
</template>
