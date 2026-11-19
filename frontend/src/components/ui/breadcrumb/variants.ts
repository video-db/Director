export const breadcrumbClasses = 'min-w-0'
export const breadcrumbListClasses = 'flex min-w-0 items-center gap-8'
export const breadcrumbItemClasses = 'flex min-w-0 items-center gap-8'
export const breadcrumbSeparatorClasses = 'text-icon-neutral-tertiary'
// chevron (default), dot or slash between steps
export type BreadcrumbSeparator = 'chevron' | 'dot' | 'slash'
// The dot fills with the icon colour (bg-current), so it follows the icon token rather than a background one
export const breadcrumbDotClasses = 'size-4 shrink-0 rounded-full bg-current text-icon-neutral-tertiary'
export const breadcrumbSlashClasses = 'text-md text-text-neutral-tertiary'

/** The last step: the current page. */
export const breadcrumbCurrentClasses = 'flex min-w-0 items-center gap-4 text-md font-semibold text-text-neutral-primary'
export const breadcrumbCurrentIconClasses = 'text-icon-neutral-tertiary'
/** A step without an href: plain text. */
export const breadcrumbTextClasses = 'flex min-w-0 items-center gap-4 text-md font-medium text-text-neutral-tertiary'
export const breadcrumbLinkClasses = 'flex min-w-0 items-center gap-4 rounded-xs text-md font-medium text-text-neutral-tertiary outline-none transition-colors duration-150 hover:text-text-neutral-primary focus-visible:shadow-focus-ring'
export const breadcrumbLabelClasses = 'truncate'
/** A step with menu items: a button that opens a Dropdown Menu, styled like a link, with a down chevron or, without a label, an ellipsis. */
export const breadcrumbTriggerClasses = `${breadcrumbLinkClasses} cursor-pointer data-[state=open]:text-text-neutral-primary`
