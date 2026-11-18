import type { ComputedRef, InjectionKey } from 'vue'
import type { InputGroupSize } from './variants'

export { default as InputGroup } from './InputGroup.vue'
export { default as InputGroupAddon } from './InputGroupAddon.vue'
export { default as InputGroupButton } from './InputGroupButton.vue'
export { default as InputGroupInput } from './InputGroupInput.vue'
export { default as InputGroupText } from './InputGroupText.vue'
export { default as InputGroupTextarea } from './InputGroupTextarea.vue'

export * from './variants'

// The group passes its size and state down, so the control, addons and buttons don't repeat them.
export interface InputGroupContext {
  size: ComputedRef<InputGroupSize>
  invalid: ComputedRef<boolean>
  disabled: ComputedRef<boolean>
  readonly: ComputedRef<boolean>
}
export const inputGroupKey: InjectionKey<InputGroupContext> = Symbol('input-group')
