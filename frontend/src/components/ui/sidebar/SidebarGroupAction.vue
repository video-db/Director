<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { sidebarGroupActionClasses } from '.'

// A 24px icon button at the end of the group's label, e.g. add. Hidden on the icon rail.
const props = defineProps<{
  /** Material Symbols name */
  icon: string
  /** Required: says what it does, e.g. "Add project" */
  label: string
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <button
    data-slot="sidebar-group-action"
    type="button"
    :aria-label="label"
    :class="cn(sidebarGroupActionClasses, props.class)"
  >
    <slot>
      <Icon :name="icon" :size="16" />
    </slot>
  </button>
</template>
