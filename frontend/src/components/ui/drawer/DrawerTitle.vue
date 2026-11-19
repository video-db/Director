<script setup lang="ts">
import type { DialogTitleProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DialogTitle } from 'reka-ui'
import { cn } from '@/lib/utils'
import { drawerTitleClasses } from '.'

// Names the drawer for screen readers. Every drawer needs one.
const props = defineProps<DialogTitleProps & { class?: HTMLAttributes['class'] }>()
const delegated = reactiveOmit(props, 'class')
</script>

<template>
  <DialogTitle data-slot="drawer-title" v-bind="delegated" :class="cn(drawerTitleClasses, props.class)">
    <slot />
  </DialogTitle>
</template>
