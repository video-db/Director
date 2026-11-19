<script setup lang="ts">
import type { DialogDescriptionProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DialogDescription } from 'reka-ui'
import { cn } from '@/lib/utils'
import { drawerDescriptionClasses } from '.'

// Describes the drawer for screen readers. Add class="sr-only" to hide it visually.
const props = defineProps<DialogDescriptionProps & { class?: HTMLAttributes['class'] }>()
const delegated = reactiveOmit(props, 'class')
</script>

<template>
  <DialogDescription data-slot="drawer-description" v-bind="delegated" :class="cn(drawerDescriptionClasses, props.class)">
    <slot />
  </DialogDescription>
</template>
