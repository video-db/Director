export type AlertStatus = 'info' | 'success' | 'warning' | 'error'

// Alert and Toast share these per-status styles.
export const statusStyles: Record<AlertStatus, { box: string, icon: string, glyph: string }> = {
  info: { box: 'bg-background-info-subtle border-border-info-primary', icon: 'text-icon-info-primary', glyph: 'info' },
  success: { box: 'bg-background-success-subtle border-border-success-primary', icon: 'text-icon-success-primary', glyph: 'check_circle' },
  warning: { box: 'bg-background-warning-subtle border-border-warning-primary', icon: 'text-icon-warning-primary', glyph: 'warning' },
  error: { box: 'bg-background-error-subtle border-border-error-primary', icon: 'text-icon-error-primary', glyph: 'error' },
}

// Alert also has two looks of its own, not shared with Toast. neutral: a grey box with no icon unless you
// give one. destructive: the same grey box with the error icon and the text in error red.
export type AlertTone = AlertStatus | 'neutral' | 'destructive'

const neutralBox = 'bg-background-neutral-subtle border-border-neutral-primary'
export const alertStyles: Record<AlertTone, { box: string, icon: string, glyph?: string }> = {
  ...statusStyles,
  neutral: { box: neutralBox, icon: 'text-icon-neutral-primary' },
  destructive: { box: `${neutralBox} text-text-error-primary`, icon: 'text-icon-error-primary', glyph: 'error' },
}

/** The alert box: add the tone's box classes. Parts style themselves by its data-status. */
export const alertClasses = 'group/alert flex w-full items-start gap-8 rounded-xs border p-12 text-text-neutral-primary'
// The message, or an AlertTitle and AlertDescription. Its colour comes from the box, so destructive turns it red.
export const alertMessageClasses = 'min-w-0 flex-1 text-sm font-medium'
export const alertTitleClasses = 'font-medium'
export const alertDescriptionClasses = 'mt-4 font-normal text-text-neutral-secondary group-data-[status=destructive]/alert:text-text-error-primary'
export const alertActionClasses = 'shrink-0'
