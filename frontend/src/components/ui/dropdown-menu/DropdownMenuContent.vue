<script setup lang="ts">
import type { DropdownMenuContentEmits, DropdownMenuContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { DropdownMenuContent, DropdownMenuPortal, useForwardPropsEmits } from 'reka-ui'
import { cn } from '@/lib/utils'
import { menuContentClasses } from '.'

// Attributes (id, data-*, aria-*) go to the panel, not the portal.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<DropdownMenuContentProps & { class?: HTMLAttributes['class'] }>(), {
  sideOffset: 4,
  align: 'start',
})
const emits = defineEmits<DropdownMenuContentEmits>()
const delegated = reactiveOmit(props, 'class')
const forwarded = useForwardPropsEmits(delegated, emits)
</script>

<template>
  <DropdownMenuPortal>
    <DropdownMenuContent data-slot="dropdown-menu-content" v-bind="{ ...forwarded, ...$attrs }" :class="cn(menuContentClasses, 'max-h-(--reka-dropdown-menu-content-available-height) origin-(--reka-dropdown-menu-content-transform-origin)', props.class)">
      <slot />
    </DropdownMenuContent>
  </DropdownMenuPortal>
</template>
