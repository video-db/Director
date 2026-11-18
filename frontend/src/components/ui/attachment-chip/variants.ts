export const attachmentChipClasses = [
  'flex w-320 max-w-full items-center gap-8 rounded-xs border border-border-neutral-primary bg-background-neutral-subtle p-8',
  'data-error:border-border-error-primary',
]
export const attachmentChipGlyphClasses = 'flex size-32 shrink-0 items-center justify-center rounded-xs border border-border-neutral-primary bg-background-neutral-primary'
export const attachmentChipIconClasses = 'text-icon-neutral-secondary'
export const attachmentChipErrorIconClasses = 'text-icon-error-primary'
export const attachmentChipTextClasses = 'flex min-w-0 flex-1 flex-col gap-2'
export const attachmentChipNameClasses = 'truncate text-sm font-medium text-text-neutral-primary'
export const attachmentChipMetaClasses = 'truncate text-xs font-medium text-text-neutral-tertiary'
/** The role="alert" message: shown with an error, otherwise visually hidden (and empty) */
export const attachmentChipErrorClasses = 'truncate text-xs font-medium text-text-error-primary'
export const attachmentChipHiddenClasses = 'sr-only'

/** The glyph for each kind */
export const attachmentChipGlyph = { video: 'movie', audio: 'headphones', image: 'image', file: 'description' } as const
