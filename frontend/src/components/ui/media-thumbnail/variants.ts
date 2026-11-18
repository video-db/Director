export const mediaThumbnailClasses = [
  'group/thumb relative flex w-full flex-col gap-8 rounded-md border border-transparent p-12 transition-colors duration-150',
  // Ring around the card while the title has keyboard focus, so the focused ⋮ button keeps just its own ring
  'hover:bg-background-neutral-hover has-[[data-slot=media-thumbnail-title]:focus-visible]:shadow-focus-ring',
  // Selected: a quiet grey a step darker than hover, with a border, so it reads in a grid of cards without shouting
  'data-selected:border-border-neutral-hover data-selected:bg-background-neutral-pressed data-selected:hover:bg-background-neutral-pressed',
]
export const mediaThumbnailMediaClasses = 'relative aspect-video w-full overflow-hidden rounded-sm bg-background-neutral-inverse-secondary'
export const mediaThumbnailImageClasses = 'absolute inset-0 size-full object-cover'
/** Play affordance: shows on hover and when the title has keyboard focus, as in the console */
export const mediaThumbnailPlayClasses = 'absolute top-1/2 left-1/2 flex size-48 -translate-1/2 items-center justify-center rounded-full border border-background-overlay-light bg-background-overlay-glass text-icon-neutral-inverse-primary opacity-0 backdrop-blur-sm transition-opacity duration-150 group-hover/thumb:opacity-100 group-has-[[data-slot=media-thumbnail-title]:focus-visible]/thumb:opacity-100'
export const mediaThumbnailAudioClasses = 'absolute top-1/2 left-1/2 -translate-1/2 text-icon-neutral-inverse-primary'
export const mediaThumbnailDurationClasses = 'absolute right-8 bottom-8'
export const mediaThumbnailRowClasses = 'flex min-h-20 items-center gap-8'
/** The title: a link or button whose ::after stretches over the whole card */
export const mediaThumbnailTitleClasses = 'min-w-0 flex-1 cursor-pointer truncate text-left text-sm text-text-neutral-primary outline-none after:absolute after:inset-0 after:rounded-md'
/** Footer and actions sit above the stretched title */
export const mediaThumbnailFooterClasses = 'relative z-10 shrink-0'
export const mediaThumbnailActionsClasses = 'relative z-10 flex items-center gap-8'
export const mediaThumbnailMenuButtonClasses = 'absolute top-16 right-16 z-10 bg-background-overlay-scrim'
