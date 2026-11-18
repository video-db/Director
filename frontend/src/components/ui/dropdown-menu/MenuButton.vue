<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import type { MenuButtonVariants } from '.'
import { menuButtonChevronClasses, menuButtonIconClasses, menuButtonVariants } from '.'

// Put it inside <DropdownMenuTrigger as-child>.
const props = defineProps<{
  /** Material Symbols name shown before the label */
  icon?: string
  /** sm: 36px. md: 40px, as in the Media Library toolbar. */
  size?: MenuButtonVariants['size']
  disabled?: boolean
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <button
    data-slot="menu-button"
    type="button"
    :disabled="disabled"
    :class="cn(menuButtonVariants({ size }), props.class)"
  >
    <!-- 16px leading icon with 8px to the label; 4px between the label and the chevron -->
    <Icon v-if="icon" :name="icon" :size="16" :class="menuButtonIconClasses" />
    <slot />
    <Icon name="keyboard_arrow_down" :class="menuButtonChevronClasses" />
  </button>
</template>
