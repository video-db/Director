<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { DurationLabel } from '@/components/ui/duration-label'
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Icon } from '@/components/ui/icon'
import { IconButton } from '@/components/ui/icon-button'
import { cn } from '@/lib/utils'
import {
  mediaThumbnailActionsClasses,
  mediaThumbnailAudioClasses,
  mediaThumbnailClasses,
  mediaThumbnailDurationClasses,
  mediaThumbnailFooterClasses,
  mediaThumbnailImageClasses,
  mediaThumbnailMediaClasses,
  mediaThumbnailMenuButtonClasses,
  mediaThumbnailPlayClasses,
  mediaThumbnailRowClasses,
  mediaThumbnailTitleClasses,
} from '.'

// The title is a stretched link/button covering the card, so the menu button can sit on top of it.
const props = withDefaults(defineProps<{
  title: string
  type?: 'video' | 'clip' | 'audio' | 'image'
  /** Poster or image URL */
  src?: string
  /** Seconds or a ready-made string. Not shown for images. */
  duration?: number | string
  selected?: boolean
  /** Makes the card a link; otherwise it is a button that emits "select" */
  href?: string
  /** Accessible label for the menu button. Defaults to "More actions for <title>". */
  menuLabel?: string
  class?: HTMLAttributes['class']
}>(), {
  type: 'video',
})

const emit = defineEmits<{ select: [] }>()
</script>

<template>
  <div
    data-slot="media-thumbnail"
    :data-selected="selected ? '' : undefined"
    :class="cn(mediaThumbnailClasses, props.class)"
  >
    <div :class="mediaThumbnailMediaClasses">
      <img v-if="src" :src="src" alt="" :class="mediaThumbnailImageClasses">
      <!-- Play affordance shows on hover and when the title has keyboard focus, as in the console -->
      <span
        v-if="type === 'video' || type === 'clip'"
        aria-hidden="true"
        :class="mediaThumbnailPlayClasses"
      >
        <Icon name="play_arrow" :size="24" filled />
      </span>
      <Icon
        v-else-if="type === 'audio'"
        name="headphones"
        :size="40"
        aria-hidden="true"
        :class="mediaThumbnailAudioClasses"
      />
      <DurationLabel v-if="duration !== undefined && type !== 'image'" :value="duration" :class="mediaThumbnailDurationClasses" />
    </div>

    <div :class="mediaThumbnailRowClasses">
      <component
        :is="href ? 'a' : 'button'"
        data-slot="media-thumbnail-title"
        :href="href"
        :type="href ? undefined : 'button'"
        :aria-pressed="href ? undefined : !!selected"
        :aria-current="href && selected ? 'true' : undefined"
        :class="mediaThumbnailTitleClasses"
        @click="emit('select')"
      >
        {{ title }}
      </component>
      <!-- e.g. the Edit button on clips; sits above the stretched link -->
      <div v-if="$slots.footer" :class="mediaThumbnailFooterClasses">
        <slot name="footer" />
      </div>
    </div>
    <!-- A row of actions under the title, e.g. Explore indexes; sits above the stretched link -->
    <div v-if="$slots.actions" :class="mediaThumbnailActionsClasses">
      <slot name="actions" />
    </div>

    <DropdownMenu v-if="$slots.menu">
      <DropdownMenuTrigger as-child>
        <IconButton
          icon="more_vert"
          :label="menuLabel ?? `More actions for ${title}`"
          hierarchy="inverse"
          size="xs"
          shape="circle"
          :class="mediaThumbnailMenuButtonClasses"
        />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <slot name="menu" />
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>
