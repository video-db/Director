import { onMounted, onUpdated, ref } from 'vue'

/**
 * Typeahead (typing a letter to jump to an item) matches on the item's text. Reka would read the
 * whole item's textContent, which starts with the icon's ligature name ("edit Rename"), so read
 * only the label span instead. Bind `ref="label"` on the span and pass the result as textValue.
 */
export function useLabelText() {
  const label = ref<HTMLElement>()
  const text = ref<string>()
  const read = () => { text.value = label.value?.textContent?.trim() || undefined }
  onMounted(read)
  onUpdated(read)
  return { label, text }
}
