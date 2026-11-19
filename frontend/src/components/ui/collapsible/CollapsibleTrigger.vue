<script setup lang="ts">
import type { CollapsibleTriggerProps } from 'reka-ui'
import { CollapsibleTrigger, injectCollapsibleRootContext } from 'reka-ui'
import { useId } from 'vue'

// Unstyled: style it, or use as-child with a Button. It carries data-state="open" | "closed"
// for a rotating chevron (group-data-[state=open]:rotate-180).
const props = defineProps<CollapsibleTriggerProps>()

// Reka gives the content its id when the content sets up, after a trigger before it has rendered, so
// aria-controls would read "" until the first toggle. Set the id first; trigger and content both use it.
const contentId = useId()
const root = injectCollapsibleRootContext()
root.contentId ||= contentId
</script>

<template>
  <CollapsibleTrigger data-slot="collapsible-trigger" v-bind="props">
    <slot />
  </CollapsibleTrigger>
</template>
