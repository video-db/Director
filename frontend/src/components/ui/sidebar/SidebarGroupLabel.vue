<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { Primitive } from 'reka-ui'
import { inject, onBeforeUnmount, onMounted } from 'vue'
import { cn } from '@/lib/utils'
import { sidebarGroupKey } from './context'
import { sidebarGroupLabelClasses } from '.'

// The group's heading. To collapse the group, make it the trigger of a Collapsible around the group:
// <CollapsibleTrigger as-child><SidebarGroupLabel as="button">. On the icon rail it fades out.
const props = withDefaults(defineProps<PrimitiveProps & { class?: HTMLAttributes['class'] }>(), {
  as: 'div',
})

const group = inject(sidebarGroupKey, null)
onMounted(() => { if (group) group.hasLabel.value = true })
onBeforeUnmount(() => { if (group) group.hasLabel.value = false })
</script>

<template>
  <Primitive
    :id="group?.labelId"
    data-slot="sidebar-group-label"
    :as="as"
    :as-child="asChild"
    :type="as === 'button' && !asChild ? 'button' : undefined"
    :class="cn(sidebarGroupLabelClasses, props.class)"
  >
    <slot />
  </Primitive>
</template>
