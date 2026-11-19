export { default as Breadcrumb } from './Breadcrumb.vue'
export * from './variants'

/** A link in a step's menu */
export interface BreadcrumbMenuItem {
  label: string
  href: string
}

export interface BreadcrumbStep {
  /** Leave it out, with items, for a collapsed step: an ellipsis that opens the hidden steps */
  label?: string
  /** Link target. The last step is the current page and is never a link. */
  href?: string
  /** Material Symbols name shown before the label */
  icon?: string
  /** Turns the step into a button that opens a menu of these links (not on the last step) */
  items?: BreadcrumbMenuItem[]
}
