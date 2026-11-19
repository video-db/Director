<script setup lang="ts">
import type { TabsRootEmits, TabsRootProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TabsRoot, useForwardPropsEmits } from 'reka-ui'
import { cn } from '@/lib/utils'
import { tabsClasses } from './variants'

// Vue reads a missing boolean prop as false, so Reka's own defaults are restated: panels that aren't
// selected leave the DOM unless TabsContent has forceMount.
const props = withDefaults(defineProps<TabsRootProps & { class?: HTMLAttributes['class'] }>(), { unmountOnHide: true })
const emits = defineEmits<TabsRootEmits>()
const delegated = reactiveOmit(props, 'class')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <TabsRoot data-slot="tabs" v-bind="forwarded" :class="cn(tabsClasses, props.class)">
    <slot />
  </TabsRoot>
</template>
