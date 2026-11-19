export { default as SegmentedControl } from './SegmentedControl.vue'
export * from './variants'

export interface SegmentedControlOption {
  value: string
  label: string
  /** Material Symbols name */
  icon?: string
  disabled?: boolean
}
