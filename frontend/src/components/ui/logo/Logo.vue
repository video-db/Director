<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, useAttrs } from 'vue'
import { cn } from '@/lib/utils'
import { logoClasses } from './variants'

// SVGs live in /public/logos. Other attributes (aria-hidden, loading…) go to the image. theme="auto"
// renders two images, so they go to both, except id, which only the light one takes so it stays unique.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  brand?: 'videodb' | 'director'
  lockup?: 'combination' | 'icon'
  /** auto follows the theme (dark artwork inside .dark). light = for light backgrounds, dark = for dark backgrounds. */
  theme?: 'auto' | 'light' | 'dark'
  /** Height in px. Width follows the artwork's ratio. */
  height?: number
  class?: HTMLAttributes['class']
}>(), {
  brand: 'videodb',
  lockup: 'combination',
  theme: 'auto',
  height: 24,
})

const srcFor = (theme: 'light' | 'dark') => `/logos/${props.brand}-${props.lockup === 'icon' ? 'icon' : 'logo'}-${theme}.svg`
const alt = computed(() => (props.brand === 'videodb' ? 'VideoDB' : 'Director'))
const attrs = useAttrs()
const darkAttrs = computed(() => {
  const { id: _id, ...rest } = attrs
  return rest
})

// auto switches on the .dark class the tokens use, not the project's dark: variant, which with
// tokens.scoped.css can follow the OS setting instead.
</script>

<template>
  <template v-if="theme === 'auto'">
    <img data-slot="logo" :src="srcFor('light')" :alt="alt" :style="{ height: `${height}px` }" :class="cn(logoClasses.autoLight, props.class)" v-bind="attrs">
    <img data-slot="logo" :src="srcFor('dark')" :alt="alt" :style="{ height: `${height}px` }" :class="cn(logoClasses.autoDark, props.class)" v-bind="darkAttrs">
  </template>
  <img v-else data-slot="logo" :src="srcFor(theme)" :alt="alt" :style="{ height: `${height}px` }" :class="cn(logoClasses.fixed, props.class)" v-bind="attrs">
</template>
