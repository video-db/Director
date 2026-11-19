import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

// A sidebar for any app: SidebarProvider holds the open state, Sidebar is the panel, and the parts
// inside it (header, scrolling content, groups, menus, footer) are composed freely. The panel collapses
// off-canvas or to an icon rail, and opens as a drawer on small screens.
//
// The panel carries data-state="expanded" | "collapsed", data-collapsible (the mode, while collapsed),
// data-variant and data-side, and is the group/sidebar the parts read, e.g.
// group-data-[collapsible=icon]/sidebar:hidden.

export type SidebarSide = 'left' | 'right'
export type SidebarVariant = 'sidebar' | 'floating' | 'inset'
export type SidebarCollapsible = 'offcanvas' | 'icon' | 'none'

/** Below 768px the sidebar opens as a drawer */
export const sidebarMobileQuery = '(max-width: 767px)'
/** Cmd+B on Mac, Ctrl+B elsewhere, toggles the sidebar */
export const sidebarKeyboardShortcut = 'b'

// The widths are variables, so a class changes them, e.g. [--sidebar-width:320px] on the provider.
// It fills the screen's height; give it a height (h-560 min-h-0) to put it in a card.
export const sidebarProviderClasses = [
  'group/sidebar-wrapper flex min-h-svh w-full',
  '[--sidebar-width:256px] [--sidebar-width-icon:48px] [--sidebar-width-mobile:288px]',
  'has-[>[data-slot=sidebar][data-variant=inset]]:bg-background-neutral-subtle',
]

/**
 * The panel on wide screens. It stays in the page's flow, so it pushes the content over, and sticks to
 * the top of a long page. Its width animates; the inner panel keeps its own width, so it slides out.
 */
export const sidebarClasses = [
  'group/sidebar sticky top-0 hidden h-svh max-h-full shrink-0 overflow-hidden text-text-neutral-primary md:flex',
  'w-(--sidebar-width) transition-[width,padding] duration-200 ease-linear motion-reduce:transition-none',
  'data-[side=left]:justify-end',
  'data-[variant=floating]:p-8 data-[variant=inset]:p-8',
  // Collapsed off-canvas: no width and (floating, inset) no padding, which would otherwise leave a 16px strip
  'data-[collapsible=offcanvas]:w-0 data-[variant=floating]:data-[collapsible=offcanvas]:p-0 data-[variant=inset]:data-[collapsible=offcanvas]:p-0',
  'data-[collapsible=icon]:w-(--sidebar-width-icon) data-[variant=floating]:data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+16px)] data-[variant=inset]:data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+16px)]',
]
export const sidebarInnerClasses = [
  'relative flex h-full w-(--sidebar-width) shrink-0 flex-col bg-background-neutral-subtle',
  'transition-[width,visibility] duration-200 ease-linear motion-reduce:transition-none',
  'group-data-[collapsible=icon]/sidebar:w-(--sidebar-width-icon)',
  // Hidden once slid out, so its controls leave the Tab order
  'group-data-[collapsible=offcanvas]/sidebar:invisible',
  'group-data-[variant=sidebar]/sidebar:border-border-neutral-primary group-data-[variant=sidebar]/sidebar:group-data-[side=left]/sidebar:border-r group-data-[variant=sidebar]/sidebar:group-data-[side=right]/sidebar:border-l',
  'group-data-[variant=floating]/sidebar:w-[calc(var(--sidebar-width)-16px)] group-data-[variant=floating]/sidebar:rounded-sm group-data-[variant=floating]/sidebar:border group-data-[variant=floating]/sidebar:border-border-neutral-primary group-data-[variant=floating]/sidebar:shadow-sm',
  'group-data-[variant=inset]/sidebar:w-[calc(var(--sidebar-width)-16px)]',
  // The icon rail's width wins over the floating and inset widths
  'group-data-[variant=floating]/sidebar:group-data-[collapsible=icon]/sidebar:w-(--sidebar-width-icon) group-data-[variant=inset]/sidebar:group-data-[collapsible=icon]/sidebar:w-(--sidebar-width-icon)',
]
/** collapsible="none": a plain panel that never collapses, also on small screens */
export const sidebarStaticClasses = 'relative flex h-full w-(--sidebar-width) shrink-0 flex-col bg-background-neutral-subtle text-text-neutral-primary'
/** On small screens the panel is a drawer from its side; the width comes from --sidebar-width-mobile */
export const sidebarMobileClasses = 'w-(--sidebar-width-mobile) max-w-[85%] gap-0 bg-background-neutral-subtle p-0 sm:max-w-[85%]'

/** The toggle button: a tertiary 32px Icon Button with a 20px icon */
export const sidebarTriggerClasses = 'size-control-xs'

/**
 * A thin hit area along the panel's inner edge: it collapses the panel, and expands it again from the icon
 * rail. An off-canvas panel is hidden once collapsed, rail and all, so the trigger brings it back. A 2px line
 * shows on hover.
 */
export const sidebarRailClasses = [
  'absolute inset-y-0 z-20 hidden w-8 outline-none sm:flex',
  'after:absolute after:inset-y-0 after:w-2 hover:after:bg-border-neutral-hover',
  'group-data-[side=left]/sidebar:right-0 group-data-[side=left]/sidebar:after:right-0 group-data-[side=right]/sidebar:left-0 group-data-[side=right]/sidebar:after:left-0',
  'group-data-[side=left]/sidebar:cursor-w-resize group-data-[side=right]/sidebar:cursor-e-resize',
  'group-data-[side=left]/sidebar:group-data-[state=collapsed]/sidebar:cursor-e-resize group-data-[side=right]/sidebar:group-data-[state=collapsed]/sidebar:cursor-w-resize',
]

/**
 * The page next to the sidebar. With variant="inset" it becomes a raised card with an 8px margin, none on
 * the sidebar's side (8px again once the panel is off-canvas). Keyed on the provider, so the panel can
 * come before or after the page.
 */
export const sidebarInsetClasses = [
  'relative flex w-full min-w-0 flex-1 flex-col bg-background-neutral-primary',
  'md:group-has-[>[data-slot=sidebar][data-variant=inset]]/sidebar-wrapper:m-8 md:group-has-[>[data-slot=sidebar][data-variant=inset]]/sidebar-wrapper:rounded-sm md:group-has-[>[data-slot=sidebar][data-variant=inset]]/sidebar-wrapper:shadow-sm',
  'md:group-has-[>[data-slot=sidebar][data-variant=inset][data-side=left]]/sidebar-wrapper:ml-0 md:group-has-[>[data-slot=sidebar][data-variant=inset][data-side=right]]/sidebar-wrapper:mr-0',
  'md:group-has-[>[data-slot=sidebar][data-variant=inset][data-side=left][data-collapsible=offcanvas]]/sidebar-wrapper:ml-8 md:group-has-[>[data-slot=sidebar][data-variant=inset][data-side=right][data-collapsible=offcanvas]]/sidebar-wrapper:mr-8',
]

export const sidebarHeaderClasses = 'flex flex-col gap-8 p-8'
export const sidebarFooterClasses = 'flex flex-col gap-8 p-8'
/** The scrolling middle. It scrolls up and down only, also on the icon rail, where the labels are clipped. */
export const sidebarContentClasses = 'flex min-h-0 flex-1 flex-col overflow-x-hidden overflow-y-auto'
export const sidebarSeparatorClasses = 'mx-8 h-px w-auto shrink-0 bg-border-neutral-primary'

export const sidebarGroupClasses = 'relative flex w-full min-w-0 flex-col p-8'
/** On the icon rail the label fades and slides up out of the way */
export const sidebarGroupLabelClasses = [
  'flex h-32 w-full shrink-0 items-center gap-8 rounded-xs px-8 text-left text-xs font-medium text-text-neutral-tertiary outline-none',
  'transition-[margin,opacity,visibility] duration-200 ease-linear motion-reduce:transition-none focus-visible:shadow-focus-ring',
  '[&>[data-slot=icon]]:shrink-0',
  // As a button (a collapsible group's trigger)
  '[button&]:cursor-pointer [button&]:hover:text-text-neutral-primary',
  'group-data-[collapsible=icon]/sidebar:invisible group-data-[collapsible=icon]/sidebar:-mt-32 group-data-[collapsible=icon]/sidebar:opacity-0',
]
/** A 24px icon button at the label's end, e.g. add, with a 16px icon */
export const sidebarGroupActionClasses = [
  'absolute top-12 right-10 flex size-24 cursor-pointer items-center justify-center rounded-xxs text-icon-neutral-primary outline-none transition-colors',
  'hover:bg-background-neutral-secondary focus-visible:shadow-focus-ring',
  // A bigger hit area on touch screens
  'after:absolute after:-inset-8 md:after:hidden',
  'group-data-[collapsible=icon]/sidebar:hidden',
]
export const sidebarGroupContentClasses = 'w-full text-sm'

export const sidebarMenuClasses = 'flex w-full min-w-0 flex-col'
export const sidebarMenuItemClasses = 'group/menu-item relative'

export const sidebarMenuButtonVariants = cva(
  [
    'peer/menu-button flex w-full cursor-pointer items-center gap-8 overflow-hidden rounded-xs p-8 text-left text-text-neutral-primary outline-none',
    'transition-[width,height,padding,background-color] duration-150 ease-linear motion-reduce:transition-none',
    'hover:bg-background-neutral-secondary focus-visible:shadow-focus-ring active:bg-background-neutral-tertiary',
    'data-active:bg-background-neutral-secondary data-active:font-medium data-active:active:bg-background-neutral-tertiary data-[state=open]:hover:bg-background-neutral-secondary',
    'disabled:pointer-events-none disabled:text-text-neutral-disabled aria-disabled:pointer-events-none aria-disabled:text-text-neutral-disabled',
    '[&>[data-slot=icon]]:shrink-0 [&>[data-slot=icon]]:text-icon-neutral-primary disabled:[&>[data-slot=icon]]:text-icon-neutral-disabled aria-disabled:[&>[data-slot=icon]]:text-icon-neutral-disabled',
    // Text spans truncate; icons (a trailing chevron too) keep their size
    '[&>span:not([data-slot=icon])]:truncate',
    // Room for a menu action or badge
    'group-has-[>[data-slot=sidebar-menu-action]]/menu-item:pr-32 group-has-[>[data-slot=sidebar-menu-badge]]/menu-item:pr-32',
    // On the icon rail: a 32px square around the 20px icon
    'group-data-[collapsible=icon]/sidebar:size-32! group-data-[collapsible=icon]/sidebar:p-6!',
  ],
  {
    variants: {
      variant: {
        default: '',
        outline: 'border border-border-neutral-primary bg-background-neutral-primary',
      },
      size: {
        sm: 'h-28 text-xs',
        md: 'h-32 text-sm',
        // Two lines, e.g. a workspace or account with a 32px logo or avatar, which fills the icon rail's square
        lg: 'h-48 text-sm group-data-[collapsible=icon]/sidebar:p-0!',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  },
)
export type SidebarMenuButtonVariants = VariantProps<typeof sidebarMenuButtonVariants>

/** A 24px icon button at the item's end, e.g. a more_horiz menu, with a 16px icon. It lines up with the button's size. */
export const sidebarMenuActionClasses = [
  'absolute top-4 right-4 flex size-24 cursor-pointer items-center justify-center rounded-xxs text-icon-neutral-primary outline-none transition-[opacity,background-color]',
  'hover:bg-background-neutral-tertiary focus-visible:shadow-focus-ring',
  'after:absolute after:-inset-8 md:after:hidden',
  'peer-data-[size=sm]/menu-button:top-2 peer-data-[size=lg]/menu-button:top-12',
  'group-data-[collapsible=icon]/sidebar:hidden',
]
/** showOnHover: hidden until the item is hovered or has focus, while its menu is open, and on the active item. Always shown on touch screens. */
export const sidebarMenuActionHoverClasses = 'pointer-fine:opacity-0 group-focus-within/menu-item:opacity-100 group-hover/menu-item:opacity-100 aria-expanded:opacity-100 data-[state=open]:opacity-100 peer-data-active/menu-button:opacity-100'

/** A count at the item's end. It sits over the button, so clicks go through to it. */
export const sidebarMenuBadgeClasses = [
  'pointer-events-none absolute top-6 right-4 flex h-20 min-w-20 items-center justify-center rounded-xxs px-4 text-xs font-medium text-text-neutral-secondary tabular-nums select-none',
  'peer-data-[size=sm]/menu-button:top-4 peer-data-[size=lg]/menu-button:top-14',
  'group-data-[collapsible=icon]/sidebar:hidden',
]

/** A loading row the size of a md menu button */
export const sidebarMenuSkeletonClasses = 'flex h-32 items-center gap-8 rounded-xs px-8'
export const sidebarMenuSkeletonIconClasses = 'size-16 shrink-0 rounded-xxs'
export const sidebarMenuSkeletonTextClasses = 'h-16 flex-1'

/** Nested items, indented under their parent's icon with a 1px line */
export const sidebarMenuSubClasses = 'mx-14 flex min-w-0 translate-x-px flex-col gap-4 border-l border-border-neutral-primary px-10 py-2 group-data-[collapsible=icon]/sidebar:hidden'
export const sidebarMenuSubItemClasses = 'group/menu-sub-item relative'
export const sidebarMenuSubButtonClasses = [
  'flex h-28 min-w-0 -translate-x-px cursor-pointer items-center gap-8 overflow-hidden rounded-xs px-8 text-text-neutral-primary outline-none transition-colors duration-150',
  'hover:bg-background-neutral-secondary focus-visible:shadow-focus-ring active:bg-background-neutral-tertiary',
  'data-active:bg-background-neutral-secondary data-active:font-medium',
  'data-[size=md]:text-sm data-[size=sm]:text-xs',
  'aria-disabled:pointer-events-none aria-disabled:text-text-neutral-disabled',
  '[&>[data-slot=icon]]:shrink-0 [&>[data-slot=icon]]:text-icon-neutral-primary [&>span:not([data-slot=icon])]:truncate',
  'group-data-[collapsible=icon]/sidebar:hidden',
]
