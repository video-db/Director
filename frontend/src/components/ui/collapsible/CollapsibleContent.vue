<script setup lang="ts">
import type { CollapsibleContentProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { reactiveOmit } from '@vueuse/core'
import { CollapsibleContent, injectCollapsibleRootContext } from 'reka-ui'
import { computed, ref, watch } from 'vue'
import { cn } from '@/lib/utils'
import { collapsibleContentClasses } from './variants'

// The only styling is the open/close height animation; put padding on an inner element,
// so the animation doesn't jump by the padding.
const props = defineProps<CollapsibleContentProps & { class?: HTMLAttributes['class'] }>()
const delegated = reactiveOmit(props, 'class')

// Reka keeps forceMount content in the page while closed but doesn't hide it, so it would show at full
// height. Hide it once closed, after the close animation, as React (Base UI) does.
const root = injectCollapsibleRootContext()
const content = ref<{ $el?: Element }>()
const closing = ref(false)
watch(root.open, async (open) => {
  if (open || !props.forceMount) return
  closing.value = true
  await new Promise(requestAnimationFrame)
  const running = () => (content.value?.$el?.getAnimations?.() ?? []).filter(a => a.effect?.getTiming().iterations !== Infinity)
  while (!root.open.value && running().length) await Promise.allSettled(running().map(a => a.finished))
  closing.value = false
})
const hidden = computed(() => props.forceMount && !root.open.value && !closing.value)
</script>

<template>
  <CollapsibleContent
    ref="content"
    data-slot="collapsible-content"
    v-bind="delegated"
    :class="cn(collapsibleContentClasses, props.class, hidden && 'hidden')"
  >
    <slot />
  </CollapsibleContent>
</template>
