<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { IconButton } from '@/components/ui/icon-button'
import { useCopy } from '@/lib/use-copy'
import { cn } from '@/lib/utils'
import {
  codeBlockClasses,
  codeBlockContentClasses,
  codeBlockCopyClasses,
  codeBlockHeaderClasses,
  codeBlockLanguageClasses,
  codeBlockLineClasses,
  codeBlockLineNumberClasses,
  codeBlockLinesClasses,
  codeBlockLineTextClasses,
  codeBlockPreClasses,
  codeBlockPreWrapClasses,
  codeBlockTitleClasses,
} from '.'

// Read-only code with a copy button, e.g. SDK snippets and embed code.
// Plain text: no highlighter is bundled. To add one, render its HTML into the default slot.
const props = defineProps<{
  code: string
  /** Shown in the header, e.g. "Python" or "cURL" */
  language?: string
  /** Shown in the header before the language, e.g. a filename */
  title?: string
  showLineNumbers?: boolean
  /** Wrap long lines instead of scrolling sideways */
  wrap?: boolean
  /** Scroll vertically past this height. Numbers are px. */
  maxHeight?: number | string
  /** Names the scroll area for screen readers. Defaults to the title or language. */
  label?: string
  class?: HTMLAttributes['class']
}>()

const name = computed(() => props.label ?? (props.title ?? (props.language ? `${props.language} code` : 'Code')))
const lines = computed(() => props.code.replace(/\n$/, '').split('\n'))
const maxHeightStyle = computed(() => (props.maxHeight === undefined
  ? undefined
  : { maxHeight: typeof props.maxHeight === 'number' ? `${props.maxHeight}px` : props.maxHeight }))

// The body only joins the Tab order when it can scroll, so keyboard users can scroll it.
const viewport = ref<HTMLElement>()
const scrollable = ref(false)
function measure() {
  const el = viewport.value
  if (el) scrollable.value = el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight
}
let observer: ResizeObserver | undefined
onMounted(() => {
  measure()
  observer = new ResizeObserver(measure)
  if (viewport.value) observer.observe(viewport.value)
})
watch(() => [props.code, props.wrap, props.showLineNumbers, props.maxHeight], () => nextTick(measure))

// Copying can fail (no permission, or not a secure page); say so instead of failing silently.
const { state: copyState, copy: copyText } = useCopy()
const copy = () => copyText(props.code)
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div
    data-slot="code-block"
    :class="cn(codeBlockClasses, props.class)"
  >
    <!-- Header: 2px right padding puts the 16px copy icon 12px from the edge -->
    <div
      data-slot="code-block-header"
      :class="codeBlockHeaderClasses"
    >
      <span :class="codeBlockTitleClasses">{{ title ?? language }}</span>
      <span v-if="title && language" :class="codeBlockLanguageClasses">{{ language }}</span>
      <IconButton
        :icon="{ idle: 'content_copy', copied: 'check', failed: 'error' }[copyState]"
        :label="{ idle: 'Copy code', copied: 'Copied', failed: `Couldn't copy code` }[copyState]"
        size="sm"
        shape="circle"
        :class="codeBlockCopyClasses[copyState]"
        @click="copy"
      />
      <span class="sr-only" aria-live="polite">{{ { idle: '', copied: 'Copied to clipboard', failed: `Couldn't copy. Select the code and copy it by hand.` }[copyState] }}</span>
    </div>

    <!-- With line numbers, each line is a table row. An empty line holds a newline, so a selection copied
         by hand keeps the blank line; it adds no height, and screen readers skip it. -->
    <div
      ref="viewport"
      data-slot="code-block-content"
      :role="scrollable ? 'region' : undefined"
      :aria-label="scrollable ? name : undefined"
      :tabindex="scrollable ? 0 : undefined"
      :class="codeBlockContentClasses"
      :style="maxHeightStyle"
    >
      <pre
        :class="[codeBlockPreClasses, codeBlockPreWrapClasses[wrap ? 'wrap' : 'scroll']]"
      ><slot><code v-if="showLineNumbers" :class="codeBlockLinesClasses"><span
        v-for="(line, i) in lines"
        :key="i"
        :class="codeBlockLineClasses"
      ><span aria-hidden="true" :class="codeBlockLineNumberClasses">{{ i + 1 }}</span><span :class="codeBlockLineTextClasses">{{ line || '\n' }}</span></span></code><code v-else>{{ code }}</code></slot></pre>
    </div>
  </div>
</template>
