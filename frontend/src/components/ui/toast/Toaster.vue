<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Toast from './Toast.vue'
import type { ToasterPosition } from '.'
import { statusPrefix, toasterClasses, toasterPositions, toastTransition, useToast } from '.'

// Renders the toast stack. Place it once, e.g. in app.vue. Attributes go to the stack's <section>.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  position?: ToasterPosition
  /** Key that moves focus to the stack, so toasts that stay open can be reached from anywhere */
  hotkey?: string
}>(), {
  position: 'bottom-right',
  hotkey: 'F8',
})

const { toasts, dismiss, pause, resume } = useToast()
const region = ref<HTMLElement>()

// Screen readers hear each new toast once, with its status ("Error: …"), and again when update()
// changes it (a loading toast finishing): errors and warnings interrupt, the rest wait their turn.
// Each message is added as its own node, so two toasts shown at the same moment are both read, and
// removed again after a while.
interface Announcement { id: number, text: string }
const polite = ref<Announcement[]>([])
const assertive = ref<Announcement[]>([])
let announced = new Map<number, string>()
let nextAnnouncement = 0
watch(toasts, (list) => {
  const next = new Map<number, string>()
  for (const t of list) {
    const text = [statusPrefix[t.status], t.message].filter(Boolean).join(' ')
    next.set(t.id, text)
    if (announced.get(t.id) === text) continue
    const target = t.status === 'error' || t.status === 'warning' ? assertive : polite
    const id = nextAnnouncement++
    target.value = [...target.value, { id, text }]
    setTimeout(() => { target.value = target.value.filter(a => a.id !== id) }, 7000)
  }
  announced = next
}, { immediate: true })

// Hotkey: focus the stack, then return focus where it was once the last toast closes.
let returnTo: HTMLElement | null = null
function onKeydown(e: KeyboardEvent) {
  if (e.key !== props.hotkey || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey || !toasts.value.length) return
  e.preventDefault()
  returnTo = document.activeElement as HTMLElement | null
  region.value?.focus()
}
watch(() => toasts.value.length, (n) => {
  if (n || !returnTo) return
  const active = document.activeElement
  if (!active || active === document.body || region.value?.contains(active)) returnTo.focus()
  returnTo = null
})
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  // The timers are shared, so they mustn't stay paused once the stack is gone
  resume()
})

// When the toast holding focus closes, focus moves to the next toast (or the one before it), else
// back to where it was before the hotkey, else to the stack itself, rather than to <body>.
// Runs before the DOM updates, while the closing toast is still focused.
watch(toasts, (list, before) => {
  const active = document.activeElement
  const closing = active instanceof HTMLElement ? active.closest<HTMLElement>('[data-toast-id]') : null
  if (!closing || !region.value?.contains(closing)) return
  const id = Number(closing.dataset.toastId)
  if (list.some(t => t.id === id)) return
  const ids = new Set(list.map(t => t.id))
  const index = before.findIndex(t => t.id === id)
  const next = before.slice(index + 1).find(t => ids.has(t.id)) ?? before.slice(0, index).reverse().find(t => ids.has(t.id))
  const target = next && region.value.querySelector<HTMLElement>(`[data-toast-id="${next.id}"] button`)
  if (target) target.focus()
  else if (returnTo?.isConnected) {
    returnTo.focus()
    returnTo = null
  }
  else region.value.focus()
})

// Timers run only while neither the pointer nor keyboard focus is on the stack.
let pointerInside = false
let focusInside = false
function onPointerEnter() {
  pointerInside = true
  pause()
}
function onPointerLeave() {
  pointerInside = false
  if (!focusInside) resume()
}
function onFocusIn() {
  focusInside = true
  pause()
}
function onFocusOut(e: FocusEvent) {
  if ((e.currentTarget as HTMLElement).contains(e.relatedTarget as Node)) return
  focusInside = false
  if (!pointerInside) resume()
}
// Once the last toast closes there is nothing to read, so the countdowns run again even if focus moved
// to the (empty) stack or the pointer left without a mouseleave; the next toast would otherwise wait.
watch(() => toasts.value.length, (n) => {
  if (n) return
  pointerInside = false
  focusInside = false
  resume()
})
</script>

<template>
  <div class="sr-only" aria-live="polite" aria-relevant="additions">
    <p v-for="a in polite" :key="a.id">
      {{ a.text }}
    </p>
  </div>
  <div class="sr-only" aria-live="assertive" aria-relevant="additions">
    <p v-for="a in assertive" :key="a.id">
      {{ a.text }}
    </p>
  </div>
  <section
    ref="region"
    data-slot="toaster"
    v-bind="$attrs"
    :aria-label="`Notifications (${hotkey})`"
    tabindex="-1"
    :class="[toasterClasses, toasterPositions[position]]"
    @mouseenter="onPointerEnter"
    @mouseleave="onPointerLeave"
    @focusin="onFocusIn"
    @focusout="onFocusOut"
  >
    <TransitionGroup
      :enter-from-class="toastTransition.enterFrom"
      :leave-to-class="toastTransition.leaveTo"
      :enter-active-class="toastTransition.enterActive"
      :leave-active-class="toastTransition.leaveActive"
    >
      <Toast v-for="t in toasts" :key="t.id" :data-toast-id="t.id" :status="t.status" class="pointer-events-auto" @dismiss="dismiss(t.id)">
        {{ t.message }}
      </Toast>
    </TransitionGroup>
  </section>
</template>
