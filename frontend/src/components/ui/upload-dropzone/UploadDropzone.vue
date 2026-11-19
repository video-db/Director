<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, ref } from 'vue'
import { Icon } from '@/components/ui/icon'
import { ProgressBar } from '@/components/ui/progress-bar'
import { cn } from '@/lib/utils'
import {
  uploadDropzoneButtonClasses,
  uploadDropzoneClasses,
  uploadDropzoneDescriptionClasses,
  uploadDropzoneDescriptionTones,
  uploadDropzoneGlyphClasses,
  uploadDropzoneIconTones,
  uploadDropzoneProgressClasses,
  uploadDropzoneTextClasses,
  uploadDropzoneTitleClasses,
  uploadDropzoneTitleTones,
} from '.'

const props = withDefaults(defineProps<{
  title?: string
  description?: string
  /** File input accept, e.g. "video/*,audio/*" */
  accept?: string
  multiple?: boolean
  disabled?: boolean
  /** Error message. Shows the error state and replaces the title. */
  error?: string
  /** 0–100 while uploading. Shows a progress bar. */
  progress?: number
  class?: HTMLAttributes['class']
}>(), {
  title: 'Drop files here',
  description: 'or click to browse — MP4, MOV, WAV up to 2 GB',
  multiple: true,
})

const emit = defineEmits<{ files: [files: File[]] }>()

const input = ref<HTMLInputElement>()
const dragging = ref(false)
let depth = 0

const state = computed(() => (props.error ? 'error' : dragging.value ? 'dragover' : props.progress !== undefined ? 'uploading' : 'idle'))
// Colours of the icon and title: disabled wins, then error, then drag-over.
const tone = computed(() => (props.disabled ? 'disabled' : state.value === 'error' ? 'error' : state.value === 'dragover' ? 'dragover' : 'default'))

// Like a file input's accept: MIME types ("video/mp4"), wildcards ("video/*") and extensions (".mp4").
function accepts(file: File) {
  const tokens = (props.accept ?? '').split(',').map(t => t.trim().toLowerCase()).filter(Boolean)
  if (!tokens.length) return true
  const name = file.name.toLowerCase()
  const type = file.type.toLowerCase()
  return tokens.some((t) => {
    if (t.startsWith('.')) return name.endsWith(t)
    if (t.endsWith('/*')) return type.startsWith(t.slice(0, -1))
    return type === t
  })
}

// Ignores new files while one is uploading, whether picked or dropped. Dropped files go through the
// same accept and multiple rules as the picker; nothing is emitted when none are left.
const uploading = computed(() => props.progress !== undefined)
function pick(list: FileList | null | undefined) {
  if (!list?.length || props.disabled || uploading.value) return
  const files = Array.from(list).filter(accepts)
  if (!files.length) return
  emit('files', props.multiple ? files : files.slice(0, 1))
}
// Cleared after each pick, so choosing the same file again still fires change.
function onChange(e: Event) {
  const el = e.target as HTMLInputElement
  pick(el.files)
  el.value = ''
}
// Like pick: a disabled or uploading zone doesn't light up when files are dragged over it.
function onDragEnter() {
  if (props.disabled || uploading.value) return
  depth++
  dragging.value = true
}
function onDragLeave() {
  depth = Math.max(0, depth - 1)
  if (!depth) dragging.value = false
}
function onDrop(e: DragEvent) {
  depth = 0
  dragging.value = false
  pick(e.dataTransfer?.files)
}
// Not while a file is uploading: the picker would start a second upload on top of it.
function browse() {
  if (!props.disabled && !uploading.value) input.value?.click()
}
</script>

<template>
  <!-- The whole box takes clicks and drops; the inner role="button" is what keyboard and screen-reader
       users reach. The progress bar and error announcement sit outside it, so they keep their roles. -->
  <div
    data-slot="upload-dropzone"
    :data-state="state"
    :data-disabled="disabled ? '' : undefined"
    :class="cn(uploadDropzoneClasses, props.class)"
    @click="browse"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <!-- Hidden from screen readers too: the role="button" below is the control, and opens it with click().
         That click stops here, so it doesn't reach the box (and a click listener on it) a second time. -->
    <input ref="input" type="file" class="sr-only" tabindex="-1" aria-hidden="true" :accept="accept" :multiple="multiple" :disabled="disabled" @click.stop @change="onChange">
    <div
      role="button"
      :tabindex="disabled ? -1 : 0"
      :aria-disabled="disabled || uploading || undefined"
      :class="uploadDropzoneButtonClasses"
      @keydown.enter.prevent="browse"
      @keydown.space.prevent
      @keyup.space.prevent="browse"
    >
      <span :class="uploadDropzoneGlyphClasses">
        <Icon :name="state === 'error' ? 'error' : 'upload_file'" :size="24" :class="uploadDropzoneIconTones[tone]" />
      </span>
      <div :class="uploadDropzoneTextClasses">
        <p :class="[uploadDropzoneTitleClasses, uploadDropzoneTitleTones[tone]]">
          {{ error ?? title }}
        </p>
        <p :class="[uploadDropzoneDescriptionClasses, uploadDropzoneDescriptionTones[disabled ? 'disabled' : 'enabled']]">
          {{ description }}
        </p>
      </div>
    </div>
    <span class="sr-only" role="alert">{{ error }}</span>
    <ProgressBar v-if="state === 'uploading'" :value="progress ?? 0" size="sm" show-value label="Upload progress" :class="uploadDropzoneProgressClasses" />
  </div>
</template>
