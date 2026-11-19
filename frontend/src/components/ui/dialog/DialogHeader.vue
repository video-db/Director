<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { DialogClose, DialogTitle } from 'reka-ui'
import { IconButton } from '@/components/ui/icon-button'
import { cn } from '@/lib/utils'
import { dialogHeaderClasses, headerRowClasses, headerRowNoTabsClasses, headerTabsClasses, headerTitleClasses } from '.'

// Put a TabsList in the #tabs slot for the Tabs=tabs variant.
const props = withDefaults(defineProps<{
  title: string
  /** Show the close button */
  closable?: boolean
  class?: HTMLAttributes['class']
}>(), {
  closable: true,
})
</script>

<template>
  <div data-slot="dialog-header" :class="cn(dialogHeaderClasses, props.class)">
    <div :class="[headerRowClasses, !$slots.tabs && headerRowNoTabsClasses]">
      <DialogTitle :class="headerTitleClasses">
        {{ title }}
      </DialogTitle>
      <DialogClose v-if="closable" as-child>
        <IconButton icon="close" label="Close" shape="circle" />
      </DialogClose>
    </div>
    <div v-if="$slots.tabs" :class="headerTabsClasses">
      <slot name="tabs" />
    </div>
  </div>
</template>
