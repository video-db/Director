<script setup lang="ts">
import type { TabsContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { TabsContent } from 'reka-ui'
import { cn } from '@/lib/utils'
import { tabsContentClasses } from './variants'

const props = defineProps<TabsContentProps & { class?: HTMLAttributes['class'] }>()
const delegated = reactiveOmit(props, 'class')
</script>

<template>
  <TabsContent data-slot="tabs-content" v-bind="delegated" :class="cn(tabsContentClasses, props.class)">
    <slot />
  </TabsContent>
</template>
