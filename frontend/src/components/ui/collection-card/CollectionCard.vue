<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Icon } from '@/components/ui/icon'
import { IconButton } from '@/components/ui/icon-button'
import { cn } from '@/lib/utils'
import {
  collectionCardClasses,
  collectionCardCountClasses,
  collectionCardFolderClasses,
  collectionCardImageClasses,
  collectionCardLinkClasses,
  collectionCardMenuButtonClasses,
  collectionCardPreviewClasses,
  collectionCardTextClasses,
} from '.'

const props = defineProps<{
  title: string
  /** File count. Numbers become "3 files". */
  count?: number | string
  /** Preview image; otherwise a folder glyph */
  src?: string
  selected?: boolean
  /** Makes the card a link; otherwise it is a toggle button. Either way a click emits "select". */
  href?: string
  /** Accessible label for the menu button. Defaults to "Actions for <title>". */
  menuLabel?: string
  class?: HTMLAttributes['class']
}>()

const emit = defineEmits<{ select: [] }>()
const countText = computed(() => (typeof props.count === 'number' ? `${props.count} ${props.count === 1 ? 'file' : 'files'}` : props.count))
</script>

<template>
  <div
    data-slot="collection-card"
    :data-selected="selected ? '' : undefined"
    :class="cn(collectionCardClasses, props.class)"
  >
    <span :class="collectionCardPreviewClasses">
      <img v-if="src" :src="src" alt="" :class="collectionCardImageClasses">
      <Icon v-else name="folder" :size="24" :class="collectionCardFolderClasses" />
    </span>
    <span :class="collectionCardTextClasses">
      <component
        :is="href ? 'a' : 'button'"
        data-slot="collection-card-link"
        :href="href"
        :type="href ? undefined : 'button'"
        :aria-pressed="href ? undefined : String(!!selected)"
        :aria-current="href && selected ? 'true' : undefined"
        :class="collectionCardLinkClasses"
        @click="emit('select')"
      >
        {{ title }}
      </component>
      <span v-if="countText" :class="collectionCardCountClasses">{{ countText }}</span>
    </span>
    <DropdownMenu v-if="$slots.menu">
      <DropdownMenuTrigger as-child>
        <IconButton
          icon="more_vert"
          :label="menuLabel ?? `Actions for ${title}`"
          size="sm"
          shape="circle"
          :class="collectionCardMenuButtonClasses"
        />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <slot name="menu" />
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>
