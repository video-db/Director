import type { ComputedRef, InjectionKey, Ref } from 'vue'
import type { SidebarCollapsible } from './variants'
import { inject } from 'vue'

export interface SidebarContext {
  /** "expanded" or "collapsed": the panel on wide screens */
  state: ComputedRef<'expanded' | 'collapsed'>
  open: ComputedRef<boolean>
  setOpen: (open: boolean) => void
  /** The drawer on small screens */
  openMobile: Ref<boolean>
  setOpenMobile: (open: boolean) => void
  isMobile: Readonly<Ref<boolean>>
  /** Toggles the panel, or the drawer on small screens */
  toggleSidebar: () => void
  /** The panel's id, for the trigger's aria-controls */
  panelId: string
  /** The provider's element, read for the drawer's width (the drawer is portaled out of it) */
  wrapper: Ref<HTMLElement | undefined>
  /** The Sidebar's collapsible mode, set by the Sidebar: "none" ignores toggles and shows no rail or tooltips */
  collapsible: Ref<SidebarCollapsible>
}

export const sidebarKey: InjectionKey<SidebarContext> = Symbol('sidebar')

export function injectSidebar(part: string) {
  const sidebar = inject(sidebarKey, null)
  if (!sidebar) throw new Error(`${part} must be used within a SidebarProvider.`)
  return sidebar
}

/** The sidebar's state and controls, for anything inside a SidebarProvider: a custom trigger, a menu that opens to the side on wide screens. */
export function useSidebar() {
  const { state, open, setOpen, openMobile, setOpenMobile, isMobile, toggleSidebar } = injectSidebar('useSidebar')
  return { state, open, setOpen, openMobile, setOpenMobile, isMobile, toggleSidebar }
}

export interface SidebarGroupContext {
  labelId: string
  /** Set by a SidebarGroupLabel while it is mounted, so the group is only labelled by one that exists */
  hasLabel: Ref<boolean>
}

export const sidebarGroupKey: InjectionKey<SidebarGroupContext> = Symbol('sidebar-group')
