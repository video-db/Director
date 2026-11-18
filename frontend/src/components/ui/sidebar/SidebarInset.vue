<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { Primitive } from 'reka-ui'
import { cn } from '@/lib/utils'
import { sidebarInsetClasses } from '.'

// The page beside the sidebar. With variant="inset" it is a raised card. It is the page's main landmark;
// use as="div" when the page already has one.
const props = withDefaults(defineProps<PrimitiveProps & { class?: HTMLAttributes['class'] }>(), {
  as: 'main',
})
</script>

<template>
  <Primitive data-slot="sidebar-inset" :as="as" :as-child="asChild" :class="cn(sidebarInsetClasses, props.class)">
    <slot />
  </Primitive>
</template>
