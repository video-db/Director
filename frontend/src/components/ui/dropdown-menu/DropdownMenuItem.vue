<script setup lang="ts">
import type { DropdownMenuItemEmits, DropdownMenuItemProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuItem, useForwardPropsEmits } from 'reka-ui'
import { Icon } from '@/components/ui/icon'
import { Kbd, KbdGroup, toAriaKeyshortcuts } from '@/components/ui/kbd'
import { useLabelText } from '@/lib/use-label-text'
import { cn } from '@/lib/utils'
import { listItemIconClasses } from '@/lib/floating'
import { menuItemClasses, menuItemDestructiveClasses, menuItemDestructiveIconClasses, menuItemLabelClasses } from '.'

const props = withDefaults(defineProps<DropdownMenuItemProps & {
  /** Material Symbols name shown before the label */
  icon?: string
  /** neutral, or destructive for actions like Delete */
  tone?: 'neutral' | 'destructive'
  /** Keys shown at the end, e.g. ['⌘', 'C']. A hint only: bind the shortcut in your app. */
  shortcut?: string | string[]
  class?: HTMLAttributes['class']
}>(), {
  tone: 'neutral',
})
const emits = defineEmits<DropdownMenuItemEmits>()
const delegated = reactiveOmit(props, 'class', 'icon', 'tone', 'shortcut', 'textValue')
const forwarded = useForwardPropsEmits(delegated, emits)
// Typeahead matches the label only, not the icon's ligature name.
const { label, text } = useLabelText()
</script>

<template>
  <DropdownMenuItem
    data-slot="dropdown-menu-item"
    :aria-keyshortcuts="shortcut ? toAriaKeyshortcuts(shortcut) : undefined"
    v-bind="forwarded"
    :text-value="textValue ?? text"
    :class="cn(
      menuItemClasses,
      tone === 'destructive' && menuItemDestructiveClasses,
      props.class,
    )"
  >
    <Icon
      v-if="icon"
      :name="icon"
      :class="tone === 'destructive' ? menuItemDestructiveIconClasses : listItemIconClasses"
    />
    <span ref="label" :class="menuItemLabelClasses"><slot /></span>
    <slot name="trailing">
      <KbdGroup v-if="shortcut" aria-hidden="true">
        <Kbd v-for="k in [shortcut].flat()" :key="k">
          {{ k }}
        </Kbd>
      </KbdGroup>
    </slot>
  </DropdownMenuItem>
</template>
