<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { provide, ref, useId } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarGroupKey } from './context'
import { sidebarGroupClasses } from '.'

// A section of the sidebar: a SidebarGroupLabel, an optional SidebarGroupAction and a
// SidebarGroupContent. With a label it is a group named by the label.
const props = defineProps<{ class?: HTMLAttributes['class'] }>()

const labelId = useId()
const hasLabel = ref(false)
provide(sidebarGroupKey, { labelId, hasLabel })
</script>

<template>
  <div
    data-slot="sidebar-group"
    :role="hasLabel ? 'group' : undefined"
    :aria-labelledby="hasLabel ? labelId : undefined"
    :class="cn(sidebarGroupClasses, props.class)"
  >
    <slot />
  </div>
</template>
