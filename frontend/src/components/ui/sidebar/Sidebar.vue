<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { SidebarCollapsible, SidebarSide, SidebarVariant } from '.'
import { computed, ref, watch, watchEffect } from 'vue'
import { Drawer, DrawerContent, DrawerTitle } from '@/components/ui/drawer'
import { cn } from '@/lib/utils'
import { injectSidebar } from './context'
import { sidebarClasses, sidebarInnerClasses, sidebarMobileClasses, sidebarStaticClasses } from '.'

// The panel. On wide screens it sits beside the page and collapses off-canvas or to an icon rail; on
// small screens it opens as a drawer from its side. Attributes and class go to the panel itself.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  side?: SidebarSide
  /** sidebar: flush with a border · floating: a raised card · inset: the page (SidebarInset) becomes the card */
  variant?: SidebarVariant
  /** offcanvas: slides out · icon: narrows to the icons · none: never collapses, also on small screens */
  collapsible?: SidebarCollapsible
  /** The panel's element: nav for an app's navigation, aside for side content such as filters */
  element?: 'nav' | 'aside' | 'div'
  /** Names the landmark, and the drawer on small screens */
  label?: string
  class?: HTMLAttributes['class']
}>(), {
  side: 'left',
  variant: 'sidebar',
  collapsible: 'offcanvas',
  element: 'nav',
  label: 'Main',
})

const sidebar = injectSidebar('Sidebar')
const { state, isMobile } = sidebar
// The provider's trigger, rail, shortcut and tooltips follow this panel's mode
watchEffect(() => { sidebar.collapsible.value = props.collapsible })
const openMobile = computed({ get: () => sidebar.openMobile.value, set: sidebar.setOpenMobile })
// A div is no landmark, so it takes no name
const ariaLabel = computed(() => props.element === 'div' ? undefined : props.label)

// The drawer is portaled out of the provider, so it takes the provider's mobile width as it opens
const mobileWidth = ref<string>()
watch(openMobile, (open) => {
  if (open && sidebar.wrapper.value) mobileWidth.value = getComputedStyle(sidebar.wrapper.value).getPropertyValue('--sidebar-width-mobile').trim() || undefined
})
</script>

<template>
  <component
    :is="element"
    v-if="collapsible === 'none'"
    :id="sidebar.panelId"
    v-bind="$attrs"
    data-slot="sidebar"
    :aria-label="ariaLabel"
    :class="cn(sidebarStaticClasses, props.class)"
  >
    <slot />
  </component>

  <Drawer v-else-if="isMobile" v-model:open="openMobile">
    <DrawerContent
      :side="side"
      :show-close-button="false"
      data-slot="sidebar"
      data-mobile=""
      :aria-describedby="undefined"
      :style="mobileWidth ? { '--sidebar-width-mobile': mobileWidth } : undefined"
      :class="cn(sidebarMobileClasses, props.class)"
    >
      <DrawerTitle class="sr-only">
        {{ label }}
      </DrawerTitle>
      <component :is="element" v-bind="$attrs" :aria-label="ariaLabel" class="flex size-full min-h-0 flex-col">
        <slot />
      </component>
    </DrawerContent>
  </Drawer>

  <div
    v-else
    data-slot="sidebar"
    :data-state="state"
    :data-collapsible="state === 'collapsed' ? collapsible : ''"
    :data-variant="variant"
    :data-side="side"
    :class="sidebarClasses"
  >
    <component
      :is="element"
      :id="sidebar.panelId"
      v-bind="$attrs"
      data-slot="sidebar-inner"
      :aria-label="ariaLabel"
      :class="cn(sidebarInnerClasses, props.class)"
    >
      <slot />
    </component>
  </div>
</template>
