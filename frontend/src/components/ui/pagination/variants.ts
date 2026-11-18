/** full: Previous, the page numbers and Next · pages: the page numbers only · arrows: Previous and Next only */
export type PaginationLayout = 'full' | 'pages' | 'arrows'

export const paginationClasses = 'flex'
export const paginationListClasses = 'flex flex-wrap items-center gap-8'
export const paginationPagesClasses = 'flex items-center gap-8'

// Previous and Next. The group name goes on each (group/prev, group/next) so the arrow dims while disabled.
export const paginationStepClasses = 'flex h-control-md cursor-pointer items-center gap-4 rounded-xs px-12 text-sm font-medium text-text-neutral-primary outline-none transition-colors duration-150 not-disabled:hover:bg-background-neutral-hover not-disabled:active:bg-background-neutral-pressed focus-visible:shadow-focus-ring disabled:cursor-not-allowed disabled:bg-transparent disabled:text-text-neutral-disabled'
export const paginationPrevIconClasses = 'text-icon-neutral-tertiary group-disabled/prev:text-icon-neutral-disabled'
export const paginationNextIconClasses = 'text-icon-neutral-tertiary group-disabled/next:text-icon-neutral-disabled'

// A page number; the current page (data-selected) takes a grey fill, as selection does across the library.
export const paginationPageClasses = 'flex size-control-md cursor-pointer items-center justify-center rounded-xs border border-transparent text-sm font-medium text-text-neutral-primary tabular-nums outline-none transition-colors duration-150 not-data-selected:hover:bg-background-neutral-hover not-data-selected:active:bg-background-neutral-pressed focus-visible:border-border-brand-primary focus-visible:shadow-focus-ring data-selected:bg-background-neutral-secondary'
export const paginationEllipsisClasses = 'flex size-control-md items-center justify-center text-sm font-medium text-text-neutral-tertiary'
