<script setup lang="ts">
import type { TooltipProviderProps } from 'reka-ui'
import { TooltipProvider } from 'reka-ui'

// Wrap a group of tooltips (a toolbar, the player controls) so moving between triggers opens the
// next one at once instead of waiting for the delay again.
const props = withDefaults(defineProps<TooltipProviderProps>(), {
  delayDuration: 300,
})
</script>

<template>
  <TooltipProvider v-bind="props">
    <slot />
  </TooltipProvider>
</template>
