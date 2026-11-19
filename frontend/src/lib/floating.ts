// The shared look of floating panels (menus, Select, Combobox, Popover, Hover Card) and the lists inside
// them, so every panel, row, group label and separator stays the same.

/** Panel surface: Radius/S, Border/Neutral/Primary, Dropshadow/M. Add the panel's own size and padding. */
export const floatingPanelClasses = 'z-50 rounded-sm border border-border-neutral-primary bg-background-neutral-primary shadow-md outline-none'

/** Fade and zoom in and out. Pair with the primitive's origin, e.g. origin-(--reka-popover-content-transform-origin). */
export const floatingAnimationClasses = [
  'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
  'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
]

/** A 36px row in a menu or list. Icons inside use group-data-disabled/item: for their disabled colour. */
export const listItemClasses = [
  'group/item relative flex h-control-sm shrink-0 cursor-pointer items-center gap-8 rounded-xs px-12 text-sm font-medium text-text-neutral-primary outline-none select-none',
  // Base UI highlights disabled menu items on hover; they keep no fill, as in Reka
  'not-data-disabled:data-highlighted:bg-background-neutral-hover',
  'data-disabled:cursor-not-allowed data-disabled:text-text-neutral-disabled',
]

/** Leading icon in a row: secondary, disabled with the row. */
export const listItemIconClasses = 'text-icon-neutral-secondary group-data-disabled/item:text-icon-neutral-disabled'

/** Group heading in a menu or list. */
export const listLabelClasses = 'px-12 pt-8 pb-4 text-xs font-medium text-text-neutral-tertiary select-none'

/** 1px rule between groups. */
export const separatorClasses = 'h-px shrink-0 bg-border-neutral-primary'
