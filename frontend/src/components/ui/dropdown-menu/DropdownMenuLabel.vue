<script setup lang="ts">
import type { DropdownMenuLabelProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuLabel } from 'reka-ui'
import { listLabelClasses } from '@/lib/floating'
import { cn } from '@/lib/utils'

// A heading above a set of items, styled like the Combobox group heading. Inside a
// DropdownMenuGroup or DropdownMenuRadioGroup it names the group for screen readers.
const props = defineProps<DropdownMenuLabelProps & { class?: HTMLAttributes['class'] }>()
const delegated = reactiveOmit(props, 'class')
</script>

<template>
  <DropdownMenuLabel
    data-slot="dropdown-menu-label"
    v-bind="delegated"
    :class="cn(listLabelClasses, props.class)"
  >
    <slot />
  </DropdownMenuLabel>
</template>
