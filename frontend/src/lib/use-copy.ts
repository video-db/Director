import { onBeforeUnmount, ref } from 'vue'

/**
 * Copy text to the clipboard and report what happened. Copying can fail (no permission, or not a
 * secure page), so `state` is 'failed' instead of an unhandled error. It returns to 'idle' after
 * 2 s, or 4 s after a failure so there is time to read the message.
 */
export function useCopy() {
  const state = ref<'idle' | 'copied' | 'failed'>('idle')
  let timer: ReturnType<typeof setTimeout> | undefined

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      state.value = 'copied'
    }
    catch {
      state.value = 'failed'
    }
    clearTimeout(timer)
    timer = setTimeout(() => { state.value = 'idle' }, state.value === 'failed' ? 4000 : 2000)
  }
  onBeforeUnmount(() => clearTimeout(timer))

  return { state, copy }
}
