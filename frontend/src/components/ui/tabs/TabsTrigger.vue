<script setup lang="ts">
import type { TabsTriggerProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TabsTrigger, useForwardProps } from 'reka-ui'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { tabsTriggerClasses, tabsTriggerIconSize } from './variants'

const props = defineProps<TabsTriggerProps & {
  /** Material Symbols name shown before the label */
  icon?: string
  class?: HTMLAttributes['class']
}>()

const delegated = reactiveOmit(props, 'class', 'icon')
const forwarded = useForwardProps(delegated)
</script>

<template>
  <TabsTrigger
    data-slot="tabs-trigger"
    v-bind="forwarded"
    :class="cn(tabsTriggerClasses, props.class)"
  >
    <Icon v-if="icon" :name="icon" :size="tabsTriggerIconSize" />
    <slot />
  </TabsTrigger>
</template>
