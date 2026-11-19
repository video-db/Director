<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { Icon } from '@/components/ui/icon'
import { IconButton } from '@/components/ui/icon-button'
import { cn } from '@/lib/utils'
import { messageScrollerButtonClasses, messageScrollerButtonTransition, messageScrollerClasses, messageScrollerViewportClasses } from '.'

// The scrolling chat thread. It stays pinned to the newest message while the user is at the
// bottom, and shows "Scroll to latest" once they scroll up to read older messages.
const props = withDefaults(defineProps<{
  /** Names the thread for screen readers */
  label?: string
  /** Label of the scroll-to-latest button */
  buttonLabel?: string
  /** Open at the newest message. Set false to open at the top, e.g. a shared chat read from the start. */
  startAtBottom?: boolean
  /** Within this many px of the end counts as "at the bottom" */
  threshold?: number
  /** Set while a reply streams in, so assistive tech can wait for the finished message */
  busy?: boolean
  /** Classes for the content wrapper, e.g. a max width and padding */
  contentClass?: HTMLAttributes['class']
  class?: HTMLAttributes['class']
}>(), {
  label: 'Conversation',
  buttonLabel: 'Scroll to latest',
  startAtBottom: true,
  threshold: 24,
})

// v-model:at-bottom, emitted as update:atBottom when the newest message comes into or goes out of view.
// It is output only: the scroll position decides it.
const atBottomModel = defineModel<boolean>('atBottom', { default: true })

const viewport = ref<HTMLElement>()
const content = ref<HTMLElement>()
// Kept locally too, so it is current straight away rather than after the parent re-renders
const atBottom = ref(true)
// True from a scrollToBottom() call until it lands, so the smooth scroll's in-between
// positions don't count as the user scrolling up.
let autoScrolling = false
let landTimer: ReturnType<typeof setTimeout> | undefined

function setAtBottom(value: boolean) {
  atBottom.value = value
  if (atBottomModel.value !== value) atBottomModel.value = value
}
function distanceFromBottom() {
  const el = viewport.value
  return el ? el.scrollHeight - el.scrollTop - el.clientHeight : 0
}

function scrollToBottom(smooth = true) {
  const el = viewport.value
  if (!el) return
  // A smooth scroll requested from script ignores the CSS reduced-motion rule, so check here.
  if (smooth && window.matchMedia('(prefers-reduced-motion: reduce)').matches) smooth = false
  autoScrolling = true
  setAtBottom(true)
  el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
  // Fallback for browsers without the scrollend event
  clearTimeout(landTimer)
  landTimer = setTimeout(() => { autoScrolling = false }, smooth ? 1000 : 50)
}

function onScroll() {
  const near = distanceFromBottom() <= props.threshold
  if (autoScrolling) {
    if (near) autoScrolling = false
    return
  }
  setAtBottom(near)
}
// Wheel, touch, keys or the scrollbar mean the user has taken over from a smooth scroll.
function onUserScroll() {
  autoScrolling = false
}
// Scrolling up unpins at once, before the scroll event, so streamed text can't pull the view back down.
function canScrollUp() {
  return (viewport.value?.scrollTop ?? 0) > 0
}
function onWheel(e: WheelEvent) {
  onUserScroll()
  if (e.deltaY < 0 && canScrollUp()) setAtBottom(false)
}
function onKeydown(e: KeyboardEvent) {
  onUserScroll()
  if (e.target === viewport.value && ['ArrowUp', 'PageUp', 'Home'].includes(e.key) && canScrollUp()) setAtBottom(false)
}
function onScrollEnd() {
  autoScrolling = false
  setAtBottom(distanceFromBottom() <= props.threshold)
}

// The button goes away once clicked, so focus moves to the thread instead of being lost.
function onButtonClick() {
  scrollToBottom(true)
  viewport.value?.focus({ preventScroll: true })
}

// New messages, streamed text and content that grows (images loading, a log expanding)
// keep the view pinned, but only if the user was already at the bottom.
function onContentChange() {
  if (atBottom.value) scrollToBottom(false)
  else if (distanceFromBottom() <= props.threshold) setAtBottom(true)
}

let resizeObserver: ResizeObserver | undefined
let mutationObserver: MutationObserver | undefined
onMounted(async () => {
  await nextTick()
  if (props.startAtBottom) scrollToBottom(false)
  else setAtBottom(distanceFromBottom() <= props.threshold)
  viewport.value?.addEventListener('scrollend', onScrollEnd)
  resizeObserver = new ResizeObserver(onContentChange)
  if (viewport.value) resizeObserver.observe(viewport.value)
  if (content.value) {
    resizeObserver.observe(content.value)
    mutationObserver = new MutationObserver(onContentChange)
    mutationObserver.observe(content.value, { childList: true, subtree: true, characterData: true })
  }
})
onBeforeUnmount(() => {
  clearTimeout(landTimer)
  viewport.value?.removeEventListener('scrollend', onScrollEnd)
  resizeObserver?.disconnect()
  mutationObserver?.disconnect()
})

defineExpose({ scrollToBottom, atBottom })
</script>

<template>
  <div data-slot="message-scroller" :class="cn(messageScrollerClasses, props.class)">
    <!-- role="log" is a polite live region: messages added later are read out, existing ones aren't -->
    <div
      ref="viewport"
      data-slot="message-scroller-viewport"
      role="log"
      :aria-label="label"
      :aria-busy="busy || undefined"
      tabindex="0"
      :class="messageScrollerViewportClasses"
      @scroll.passive="onScroll"
      @wheel.passive="onWheel"
      @touchstart.passive="onUserScroll"
      @keydown="onKeydown"
      @pointerdown="onUserScroll"
    >
      <div ref="content" data-slot="message-scroller-content" :class="contentClass">
        <slot />
      </div>
    </div>

    <Transition
      :enter-active-class="messageScrollerButtonTransition.enterActive"
      :enter-from-class="messageScrollerButtonTransition.enterFrom"
      :leave-active-class="messageScrollerButtonTransition.leaveActive"
      :leave-to-class="messageScrollerButtonTransition.leaveTo"
    >
      <!-- The slot keeps the 20px icon; IconButton sm would draw 16 -->
      <IconButton
        v-if="!atBottom"
        icon="arrow_downward"
        :label="buttonLabel"
        hierarchy="secondary"
        size="sm"
        shape="circle"
        data-slot="message-scroller-button"
        :class="messageScrollerButtonClasses"
        @click="onButtonClick"
      >
        <Icon name="arrow_downward" />
      </IconButton>
    </Transition>
  </div>
</template>
