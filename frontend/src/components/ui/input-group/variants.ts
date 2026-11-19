export type InputGroupSize = 'sm' | 'md' | 'lg'
export type InputGroupAddonAlign = 'inline-start' | 'inline-end' | 'block-start' | 'block-end'

// The group takes the Input field's look (inputVariants from Input) plus these.
export const inputGroupClasses = [
  'group/input-group relative',
  // A textarea or a block addon stacks the group: rows above and below the control.
  'has-[>textarea]:h-auto has-[>textarea]:flex-col has-[>textarea]:items-stretch',
  'has-[>[data-block]]:h-auto has-[>[data-block]]:flex-col has-[>[data-block]]:items-stretch',
]

/** Vertical padding of a stacked group. */
export function inputGroupStackedClasses(size: InputGroupSize) {
  return size === 'lg' ? 'has-[>textarea]:py-12 has-[>[data-block]]:py-12' : 'has-[>textarea]:py-8 has-[>[data-block]]:py-8'
}

export const inputGroupAddonClasses = [
  'flex shrink-0 cursor-text items-center gap-8 select-none',
  'text-icon-neutral-tertiary group-focus-within/input-group:text-icon-neutral-secondary',
  'group-data-disabled/input-group:cursor-not-allowed group-data-disabled/input-group:text-icon-neutral-disabled',
]

// A button at the outer edge is pulled outwards so it sits 4px from the border
// (block rows: 4px at sm and md, 8px at lg). The leading icon turns red when invalid, as in Input.
export function inputGroupAddonAlignClasses(align: InputGroupAddonAlign, size: InputGroupSize) {
  const lg = size === 'lg'
  return {
    'inline-start': ['order-first group-data-invalid/input-group:text-icon-error-primary', lg ? 'has-[>button:first-child]:-ml-12' : 'has-[>button:first-child]:-ml-8'],
    'inline-end': ['order-last', lg ? 'has-[>button:last-child]:-mr-12' : 'has-[>button:last-child]:-mr-8'],
    'block-start': 'order-first justify-start has-[>button]:-mt-4 has-[>button:first-child]:-ml-8 has-[>button:last-child]:-mr-8',
    'block-end': 'order-last justify-start has-[>button]:-mb-4 has-[>button:first-child]:-ml-8 has-[>button:last-child]:-mr-8',
  }[align]
}

// These replace Button's own height and padding (it is rendered at size sm for the 16px icon and
// Text sm): cn() merges them over its size sm classes. 28px (xs) or 32px (sm); square when icon-only.
export function inputGroupButtonClasses(size: 'xs' | 'sm', iconOnly: boolean) {
  return [
    'gap-4 rounded-xxs',
    size === 'xs' ? 'h-28' : 'h-control-xs',
    iconOnly ? (size === 'xs' ? 'w-28 px-0' : 'w-control-xs px-0') : 'px-8',
  ]
}

export const inputGroupInputClasses = [
  'h-full min-w-0 flex-1 bg-transparent outline-none placeholder:text-text-neutral-tertiary',
  'disabled:cursor-not-allowed disabled:placeholder:text-text-neutral-disabled',
  // In a stacked group (block addons) the input keeps its own height.
  'group-has-[>[data-block]]/input-group:h-control-xs group-has-[>[data-block]]/input-group:flex-none',
]

export const inputGroupTextareaClasses = [
  'block min-h-80 w-full resize-none bg-transparent outline-none placeholder:text-text-neutral-tertiary',
  'disabled:cursor-not-allowed disabled:placeholder:text-text-neutral-disabled',
]

export const inputGroupTextClasses = [
  'flex items-center gap-8 text-sm whitespace-nowrap text-text-neutral-tertiary',
  'group-data-disabled/input-group:text-text-neutral-disabled',
]
