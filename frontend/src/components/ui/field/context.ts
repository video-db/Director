import type { ComputedRef, InjectionKey } from 'vue'
import { computed, inject, onBeforeUnmount, useAttrs } from 'vue'

export interface FieldContext {
  /** id of the helper or error text, when there is one */
  messageId: ComputedRef<string | undefined>
  invalid: ComputedRef<boolean>
  /** id the label points at: the field's `for`, or a generated one */
  controlId?: ComputedRef<string>
  /** Hands controlId to the first control that asks; later controls get undefined, so ids stay unique */
  claimControlId?: () => string | undefined
  /** Gives controlId back when that control unmounts */
  releaseControlId?: () => void
}

export const fieldKey: InjectionKey<FieldContext> = Symbol('field')

/**
 * For controls inside a Field: links the field's helper/error text with aria-describedby
 * (alongside any aria-describedby passed in) and marks the control invalid when the field has an error.
 */
export function useField(invalid?: () => boolean | undefined) {
  const field = inject(fieldKey, null)
  const attrs = useAttrs()
  return {
    describedBy: computed(() => [...new Set([attrs['aria-describedby'], field?.messageId.value].filter(Boolean))].join(' ') || undefined),
    invalid: computed(() => !!invalid?.() || !!field?.invalid.value),
  }
}

/**
 * For the focusable control inside a Field: returns its own id when it has one, otherwise the
 * id the field's label points at, so the label and message are linked even when `for` is left out.
 * Only the first control without an id takes the field's id.
 */
export function useFieldId(ownId: () => string | undefined) {
  const field = inject(fieldKey, null)
  const claimed = ownId() ? undefined : field?.claimControlId?.()
  if (claimed) onBeforeUnmount(() => field?.releaseControlId?.())
  return computed(() => ownId() ?? claimed)
}
