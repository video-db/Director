<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { SidebarCollapsible } from '.'
import { useEventListener, useMediaQuery, useMounted } from '@vueuse/core'
import { computed, provide, ref, useId, watch } from 'vue'
import { TooltipProvider } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { sidebarKey } from './context'
import { sidebarMobileQuery, sidebarProviderClasses } from '.'

// Holds the open state for the Sidebar, SidebarTrigger and SidebarRail inside it, and lays the panel and
// the page (SidebarInset) out side by side. Bind v-model:open to keep the state, e.g. in a cookie.
// Attributes (style, id, data-*) go to the wrapper.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  /** Expanded on first render, when open isn't bound */
  defaultOpen?: boolean
  /** Toggles the sidebar with Cmd (Mac) or Ctrl. false turns it off, e.g. for a second sidebar on the page. */
  keyboardShortcut?: string | false
  class?: HTMLAttributes['class']
}>(), {
  defaultOpen: true,
  keyboardShortcut: 'b',
})

// undefined unless bound, so an unbound sidebar starts at defaultOpen
const model = defineModel<boolean | undefined>('open', { default: undefined })
const uncontrolled = ref(props.defaultOpen)
const open = computed(() => model.value ?? uncontrolled.value)
function setOpen(value: boolean) {
  uncontrolled.value = value
  model.value = value
}

// false until mounted, as on the server, so a phone hydrates the same markup and then switches to the drawer
const mounted = useMounted()
const matchesMobile = useMediaQuery(sidebarMobileQuery)
const isMobile = computed(() => mounted.value && matchesMobile.value)
const collapsible = ref<SidebarCollapsible>('offcanvas')
const openMobile = ref(false)
const setOpenMobile = (value: boolean) => { openMobile.value = value }
// The drawer closes when the screen widens past it
watch(isMobile, (mobile) => { if (!mobile) openMobile.value = false })

function toggleSidebar() {
  if (collapsible.value === 'none') return
  if (isMobile.value) setOpenMobile(!openMobile.value)
  else setOpen(!open.value)
}

// Cmd+B / Ctrl+B, except in a text field, where it usually means bold
// (on the window, which useEventListener uses when it isn't given a target)
useEventListener('keydown', (e: KeyboardEvent) => {
  const key = props.keyboardShortcut
  if (!key || e.key.toLowerCase() !== key.toLowerCase() || !(e.metaKey || e.ctrlKey) || e.altKey || e.shiftKey) return
  if ((e.target as HTMLElement | null)?.closest?.('input, textarea, select, [contenteditable]:not([contenteditable="false"])')) return
  e.preventDefault()
  toggleSidebar()
})

const state = computed(() => open.value ? 'expanded' as const : 'collapsed' as const)
const wrapper = ref<HTMLElement>()
// The template's TooltipProvider is shared, so moving down the icon rail shows each item's tooltip at once
provide(sidebarKey, { state, open, setOpen, openMobile, setOpenMobile, isMobile, toggleSidebar, panelId: useId(), wrapper, collapsible })
</script>

<template>
  <TooltipProvider>
    <div
      ref="wrapper"
      data-slot="sidebar-wrapper"
      v-bind="$attrs"
      :class="cn(sidebarProviderClasses, props.class)"
    >
      <slot
        :state="state"
        :open="open"
        :set-open="setOpen"
        :is-mobile="isMobile"
        :open-mobile="openMobile"
        :set-open-mobile="setOpenMobile"
        :toggle-sidebar="toggleSidebar"
      />
    </div>
  </TooltipProvider>
</template>
