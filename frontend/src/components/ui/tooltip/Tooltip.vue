<script setup lang="ts">
import type { TooltipRootEmits, TooltipRootProps } from 'reka-ui'
import { injectTooltipProviderContext, TooltipRoot, useForwardPropsEmits } from 'reka-ui'
import TooltipProvider from './TooltipProvider.vue'

// Brings its own TooltipProvider, so a single tooltip needs no setup. Inside a TooltipProvider it
// uses that one instead.
const props = defineProps<TooltipRootProps>()
const emits = defineEmits<TooltipRootEmits>()
const forwarded = useForwardPropsEmits(props, emits)

const hasProvider = !!injectTooltipProviderContext(null)
</script>

<template>
  <TooltipRoot v-if="hasProvider" v-slot="slotProps" data-slot="tooltip" v-bind="forwarded">
    <slot v-bind="slotProps" />
  </TooltipRoot>
  <TooltipProvider v-else>
    <TooltipRoot v-slot="slotProps" data-slot="tooltip" v-bind="forwarded">
      <slot v-bind="slotProps" />
    </TooltipRoot>
  </TooltipProvider>
</template>
