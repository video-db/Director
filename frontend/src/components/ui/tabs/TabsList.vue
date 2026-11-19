<script setup lang="ts">
import type { TabsListProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TabsList } from 'reka-ui'
import { cn } from '@/lib/utils'
import type { TabsListVariant } from './variants'
import { tabsListClasses } from './variants'

// Vue reads a missing boolean prop as false, so Reka's default is restated: the arrow keys wrap.
const props = withDefaults(defineProps<TabsListProps & {
  /** default: the tabs in a grey pill. line: no fill, the selected tab underlined. */
  variant?: TabsListVariant
  class?: HTMLAttributes['class']
}>(), { loop: true, variant: 'default' })
const delegated = reactiveOmit(props, 'class', 'variant')
</script>

<template>
  <TabsList
    data-slot="tabs-list"
    :data-variant="variant"
    v-bind="delegated"
    :class="cn(tabsListClasses(variant), props.class)"
  >
    <slot />
  </TabsList>
</template>
