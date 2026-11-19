// A ring (inner radius 72%) with a 225° arc that spins.
export const spinnerSizes = { xs: 12, sm: 16, md: 20, lg: 24 } as const
/** [track, arc] stroke classes per colour. current takes the text colour, e.g. inside a Button. */
export const spinnerTones = {
  brand: ['stroke-background-brand-tertiary', 'stroke-icon-brand-primary'],
  neutral: ['stroke-border-neutral-hover', 'stroke-icon-neutral-secondary'],
  inverse: ['stroke-border-neutral-inverse-primary', 'stroke-icon-neutral-inverse-primary'],
  current: ['stroke-current opacity-25', 'stroke-current'],
} as const
export type SpinnerSize = keyof typeof spinnerSizes
export type SpinnerColour = keyof typeof spinnerTones
// viewBox 24: outer radius 12, ring 3.36 thick, so the stroke centre sits at 10.32.
export const spinnerRadius = 10.32
export const spinnerStrokeWidth = 3.36
const circumference = 2 * Math.PI * spinnerRadius
/** The arc covers 62.5% of the ring. */
export const spinnerDashArray = `${circumference * 0.625} ${circumference}`
