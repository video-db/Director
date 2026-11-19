import type { ClassValue } from 'clsx'
import { clsx } from 'clsx'
import { extendTailwindMerge } from 'tailwind-merge'

// Teach tailwind-merge the VideoDB type scale, radii, shadows and control sizes (tokens.css)
// so a class passed in from outside cleanly overrides the component default.
const twMerge = extendTailwindMerge({
  extend: {
    // h-control-sm, size-control-xs… are sizes, so a class passed in replaces the default
    theme: {
      spacing: ['control-xs', 'control-sm', 'control-md', 'control-lg'],
    },
    classGroups: {
      'font-size': [{ text: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'md'] }],
      'rounded': [{ rounded: ['xxs'] }],
      'shadow': [{ shadow: ['xxs', 'full', 'focus-ring'] }],
    },
  },
})

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
