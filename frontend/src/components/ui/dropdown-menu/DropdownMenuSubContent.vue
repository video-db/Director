<script setup lang="ts">
import type { DropdownMenuSubContentEmits, DropdownMenuSubContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuPortal, DropdownMenuSubContent, useForwardPropsEmits } from 'reka-ui'
import { cn } from '@/lib/utils'
import { menuContentClasses } from '.'

// Attributes (id, data-*, aria-*) go to the panel, not the portal.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<DropdownMenuSubContentProps & { class?: HTMLAttributes['class'] }>(), {
  sideOffset: 6,
})
const emits = defineEmits<DropdownMenuSubContentEmits>()
const delegated = reactiveOmit(props, 'class')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <DropdownMenuPortal>
    <DropdownMenuSubContent data-slot="dropdown-menu-sub-content" v-bind="{ ...forwarded, ...$attrs }" :class="cn(menuContentClasses, 'max-h-(--reka-dropdown-menu-content-available-height) origin-(--reka-dropdown-menu-content-transform-origin)', props.class)">
      <slot />
    </DropdownMenuSubContent>
  </DropdownMenuPortal>
</template>
