import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export const buttonVariants = cva(
  [
    'inline-flex shrink-0 cursor-pointer items-center justify-center gap-8 whitespace-nowrap rounded-xs',
    'font-semibold transition-colors duration-150 outline-none',
    'focus-visible:shadow-focus-ring disabled:cursor-not-allowed',
  ],
  {
    variants: {
      hierarchy: {
        primary: '',
        secondary: 'border bg-background-neutral-primary',
        tertiary: 'bg-transparent',
        link: 'h-auto! px-0! bg-transparent',
      },
      destructive: {
        false: '',
        true: '',
      },
      size: {
        // 28px, as IconButton xs, for dense toolbars and table rows
        xs: 'h-28 gap-4 px-8 text-xs',
        sm: 'h-control-sm px-12 text-sm',
        md: 'h-control-md px-16 text-sm',
        lg: 'h-control-lg px-24 text-md',
      },
    },
    compoundVariants: [
      {
        hierarchy: 'primary',
        destructive: false,
        class: 'bg-background-brand-primary text-text-brand-inverse not-disabled:hover:bg-background-brand-primary-hover not-disabled:active:bg-background-brand-primary-pressed',
      },
      {
        hierarchy: 'primary',
        destructive: true,
        class: 'bg-background-error-bold text-text-error-inverse not-disabled:hover:bg-background-error-bold-hover not-disabled:active:bg-background-error-bold-pressed',
      },
      {
        hierarchy: 'primary',
        class: 'disabled:bg-background-neutral-disabled disabled:text-text-neutral-disabled',
      },
      {
        hierarchy: 'secondary',
        destructive: false,
        class: 'border-border-neutral-primary text-text-neutral-primary not-disabled:hover:border-border-neutral-hover not-disabled:hover:bg-background-neutral-hover not-disabled:hover:text-text-neutral-hover not-disabled:active:bg-background-neutral-pressed',
      },
      {
        hierarchy: 'secondary',
        destructive: true,
        class: 'border-border-error-primary text-text-error-primary not-disabled:hover:bg-background-error-subtle not-disabled:hover:text-text-error-hover not-disabled:active:bg-background-error-subtle-hover',
      },
      {
        hierarchy: 'secondary',
        class: 'disabled:border-border-neutral-primary disabled:text-text-neutral-disabled',
      },
      {
        hierarchy: 'tertiary',
        destructive: false,
        class: 'text-text-neutral-primary not-disabled:hover:bg-background-neutral-hover not-disabled:hover:text-text-neutral-hover not-disabled:active:bg-background-neutral-pressed',
      },
      {
        hierarchy: 'tertiary',
        destructive: true,
        class: 'text-text-error-primary not-disabled:hover:bg-background-error-subtle not-disabled:hover:text-text-error-hover not-disabled:active:bg-background-error-subtle-hover',
      },
      {
        hierarchy: 'tertiary',
        class: 'disabled:text-text-neutral-disabled',
      },
      {
        hierarchy: 'link',
        class: 'text-text-brand-primary not-disabled:hover:text-text-brand-hover disabled:text-text-neutral-disabled',
      },
    ],
    defaultVariants: {
      hierarchy: 'primary',
      destructive: false,
      size: 'md',
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>

/** Icon size per button size: 16px at xs and sm, 20px at md and lg. */
export const buttonIconSize = { xs: 16, sm: 16, md: 20, lg: 20 } as const
/** The loading spinner takes the icon's size and side (iconPosition). */
export const buttonSpinnerSize = { xs: 'sm', sm: 'sm', md: 'md', lg: 'md' } as const
