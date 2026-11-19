// The selected tab is marked data-state="active" (as Reka UI marks it; the React Tab sets it too). The
// root, the list and each trigger carry data-orientation; the list carries data-variant and is the
// group/tabs-list the triggers read.
export type TabsListVariant = 'default' | 'line'

/** Horizontal: the list above the panel. Vertical: the list on the left, the panel beside it. */
export const tabsClasses = 'flex gap-8 data-[orientation=horizontal]:flex-col'

/**
 * default: the tabs sit in a grey pill, like a Segmented Control, 36px tall with 4px of padding.
 * line: no fill; the selected tab is underlined.
 * The list scrolls sideways when the tabs don't fit (scrollbar hidden).
 */
export function tabsListClasses(variant: TabsListVariant) {
  return [
    // relative: Base UI scrolls the active tab into view by its offset from the list, which must be its offsetParent.
    // scroll-p keeps the focus ring in view when a tab is scrolled to the edge.
    'group/tabs-list relative inline-flex w-fit shrink-0 items-center overflow-x-auto scroll-p-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
    // The list's own data-orientation, so a nested Tabs keeps its own layout
    'data-[orientation=vertical]:h-fit data-[orientation=vertical]:flex-col data-[orientation=vertical]:items-stretch',
    variant === 'default'
      ? 'h-control-sm max-w-full gap-2 rounded-xs bg-background-neutral-secondary p-4 data-[orientation=vertical]:h-auto'
      // 4px of padding, cancelled by a negative margin, keeps the focus ring inside the scroll box; the
      // max width allows for the margin
      : '-m-4 max-w-[calc(100%+8px)] gap-4 p-4',
  ]
}

export const tabsTriggerClasses = [
  // ::after is the line variant's underline; absolute, so it is never a flex item of the trigger
  'relative inline-flex shrink-0 cursor-pointer items-center justify-center gap-8 px-12 text-sm font-medium whitespace-nowrap after:absolute',
  'text-text-neutral-tertiary outline-none transition-[color,background-color,box-shadow] duration-150',
  'not-data-disabled:hover:text-text-neutral-primary data-[state=active]:text-text-neutral-primary',
  'focus-visible:shadow-focus-ring',
  'data-disabled:cursor-not-allowed data-disabled:text-text-neutral-disabled',
  'data-[orientation=vertical]:justify-start',
  // default: a 28px segment; the selected one takes the page's fill
  'group-data-[variant=default]/tabs-list:h-28 group-data-[variant=default]/tabs-list:rounded-xs',
  'group-data-[variant=default]/tabs-list:data-[state=active]:bg-background-neutral-primary group-data-[variant=default]/tabs-list:data-[state=active]:shadow-xxs',
  // line: a 36px tab with a 2px line in the text colour under it (beside it when vertical)
  'group-data-[variant=line]/tabs-list:h-control-sm group-data-[variant=line]/tabs-list:rounded-xxs',
  'group-data-[variant=line]/tabs-list:after:bg-current group-data-[variant=line]/tabs-list:after:opacity-0 group-data-[variant=line]/tabs-list:after:transition-opacity',
  'group-data-[variant=line]/tabs-list:data-[state=active]:after:opacity-100',
  'data-[orientation=horizontal]:after:inset-x-0 data-[orientation=horizontal]:after:bottom-0 data-[orientation=horizontal]:after:h-2',
  'data-[orientation=vertical]:after:inset-y-0 data-[orientation=vertical]:after:right-0 data-[orientation=vertical]:after:w-2',
]
/** Tab icons are 16px, as in a Segmented Control. */
export const tabsTriggerIconSize = 16

export const tabsContentClasses = 'min-w-0 flex-1 rounded-xxs outline-none focus-visible:shadow-focus-ring'
