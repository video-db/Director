export const collectionCardClasses = [
  'relative flex w-full items-center gap-12 rounded-sm border border-border-neutral-primary bg-background-neutral-subtle p-12 transition-colors duration-150',
  // Ring on the title link only, so the focused ⋮ button keeps just its own ring
  'hover:border-border-neutral-hover hover:bg-background-neutral-secondary has-[[data-slot=collection-card-link]:focus-visible]:shadow-focus-ring',
  // Selected: the grey fill and border of a selected Media Thumbnail
  'data-selected:border-border-neutral-hover data-selected:bg-background-neutral-pressed data-selected:hover:bg-background-neutral-pressed',
]
export const collectionCardPreviewClasses = 'flex h-42 w-56 shrink-0 items-center justify-center overflow-hidden rounded-xs bg-background-brand-tertiary'
export const collectionCardImageClasses = 'size-full object-cover'
export const collectionCardFolderClasses = 'text-icon-brand-primary'
export const collectionCardTextClasses = 'flex min-w-0 flex-1 flex-col gap-4'
/** The title: a link or toggle button whose ::after stretches over the whole card */
export const collectionCardLinkClasses = 'cursor-pointer truncate text-left text-sm font-medium text-text-neutral-primary outline-none after:absolute after:inset-0 after:rounded-sm'
export const collectionCardCountClasses = 'truncate text-xs font-medium text-text-neutral-tertiary'
/** The ⋮ button sits above the stretched title */
export const collectionCardMenuButtonClasses = 'relative z-10 not-disabled:hover:bg-background-neutral-tertiary'

export const createCollectionCardClasses = [
  'flex w-full cursor-pointer items-center gap-12 rounded-sm border border-dashed border-border-neutral-hover bg-background-neutral-subtle p-12 text-left outline-none transition-colors duration-150',
  'hover:bg-background-neutral-secondary focus-visible:shadow-focus-ring',
]
export const createCollectionCardIconBoxClasses = 'flex h-42 w-56 shrink-0 items-center justify-center rounded-xs'
export const createCollectionCardIconClasses = 'text-icon-neutral-secondary'
export const createCollectionCardLabelClasses = 'min-w-0 flex-1 truncate text-sm font-medium text-text-neutral-primary'
