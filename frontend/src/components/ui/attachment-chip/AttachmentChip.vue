<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, ref, watch } from 'vue'
import { Icon } from '@/components/ui/icon'
import { IconButton } from '@/components/ui/icon-button'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import {
  attachmentChipClasses,
  attachmentChipErrorClasses,
  attachmentChipErrorIconClasses,
  attachmentChipGlyph,
  attachmentChipGlyphClasses,
  attachmentChipHiddenClasses,
  attachmentChipIconClasses,
  attachmentChipMetaClasses,
  attachmentChipNameClasses,
  attachmentChipTextClasses,
  formatBytes,
} from '.'

const props = withDefaults(defineProps<{
  name: string
  kind?: 'video' | 'audio' | 'image' | 'file'
  /** Bytes (formatted as "500 MB") or a ready-made string */
  size?: number | string
  /** 0–100 while uploading */
  progress?: number
  /** Error message; replaces the size line */
  error?: string
  removable?: boolean
  class?: HTMLAttributes['class']
}>(), {
  kind: 'video',
  removable: true,
})

const emit = defineEmits<{ remove: [] }>()

const meta = computed(() => {
  if (props.error) return props.error
  if (props.progress !== undefined) return `Uploading… ${Math.round(props.progress)}%`
  return typeof props.size === 'number' ? formatBytes(props.size) : props.size
})

const uploading = computed(() => props.progress !== undefined && !props.error)
// Remembers an upload in progress, so finishing it can be announced as "uploaded"
const wasUploading = ref(uploading.value)
watch(uploading, (now) => {
  if (now) wasUploading.value = true
})
const statusText = computed(() => {
  // The role="alert" message already announces a failure, so the status stays quiet.
  if (props.error) return ''
  if (uploading.value) return `Uploading ${props.name}`
  return wasUploading.value ? `${props.name} uploaded` : ''
})
</script>

<template>
  <div
    data-slot="attachment-chip"
    :data-error="error ? '' : undefined"
    :class="cn(attachmentChipClasses, props.class)"
  >
    <span :class="attachmentChipGlyphClasses">
      <Spinner v-if="uploading" size="sm" decorative />
      <Icon v-else :name="attachmentChipGlyph[kind]" :class="error ? attachmentChipErrorIconClasses : attachmentChipIconClasses" />
    </span>
    <span :class="attachmentChipTextClasses">
      <span :class="attachmentChipNameClasses">{{ name }}</span>
      <span v-if="meta && !error" :class="attachmentChipMetaClasses">{{ meta }}</span>
      <!-- Always rendered, so screen readers announce the message when it is set -->
      <span role="alert" :class="error ? attachmentChipErrorClasses : attachmentChipHiddenClasses">{{ error }}</span>
    </span>
    <span role="status" :class="attachmentChipHiddenClasses">{{ statusText }}</span>
    <IconButton v-if="removable" icon="close" :label="`Remove ${name}`" size="sm" shape="circle" @click="emit('remove')" />
  </div>
</template>
