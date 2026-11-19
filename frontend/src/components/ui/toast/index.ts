import type { ToastStatus } from './variants'
import { ref } from 'vue'

export { default as Toast } from './Toast.vue'
export { default as Toaster } from './Toaster.vue'
export * from './variants'

export interface ToastItem {
  id: number
  message: string
  status: ToastStatus
  /** ms before it closes; 0 keeps it open until dismissed */
  duration: number
}

/** Visually hidden text read before each message, so the status doesn't rely on icon or colour. */
export const statusPrefix: Record<ToastStatus, string> = { neutral: '', loading: 'Loading:', success: 'Success:', info: 'Info:', warning: 'Warning:', error: 'Error:' }

export interface ToastOptions {
  status?: ToastStatus
  /** ms before it closes; 0 keeps it open until dismissed */
  duration?: number
}
/** A message, or a function of the task's result (or error) that returns one */
export type ToastMessage<T> = string | ((value: T) => string)
export interface ToastPromiseMessages<T> {
  loading: string
  /** Shown when the task resolves; a function gets its result */
  success: ToastMessage<T>
  /** Shown when the task fails; a function gets the error */
  error: ToastMessage<unknown>
}

// Module-level state: one toast stack for the whole app. In an SSR app this module is shared by
// every request on the server, so only call toast() in the browser (event handlers, onMounted).
const toasts = ref<ToastItem[]>([])
let nextId = 1

// Each toast's timer, so it can pause while the pointer or focus is on the stack. A timer started
// while paused waits for resume().
const timers = new Map<number, { handle?: ReturnType<typeof setTimeout>, remaining: number, started: number }>()
let paused = false

function startTimer(id: number, ms: number) {
  timers.set(id, { handle: paused ? undefined : setTimeout(() => dismiss(id), ms), remaining: ms, started: Date.now() })
}
function stopTimer(id: number) {
  clearTimeout(timers.get(id)?.handle)
  timers.delete(id)
}

function dismiss(id: number) {
  stopTimer(id)
  toasts.value = toasts.value.filter(t => t.id !== id)
}

/** Stops every toast's countdown, e.g. while the pointer or keyboard focus is on the stack. */
function pause() {
  paused = true
  for (const t of timers.values()) {
    if (!t.handle) continue
    clearTimeout(t.handle)
    t.handle = undefined
    t.remaining -= Date.now() - t.started
  }
}

function resume() {
  paused = false
  for (const [id, t] of timers) {
    if (!t.handle) startTimer(id, Math.max(t.remaining, 1000))
  }
}

/** Errors and loading toasts stay until dismissed or updated; the rest close after 5 s. */
const defaultDuration = (status: ToastStatus) => (status === 'error' || status === 'loading' ? 0 : 5000)

/** Shows a toast and returns its id. Pass `duration` to override how long it stays. */
function show(message: string, options: ToastOptions = {}) {
  const status = options.status ?? 'neutral'
  const item: ToastItem = { id: nextId++, message, status, duration: options.duration ?? defaultDuration(status) }
  toasts.value = [...toasts.value, item]
  if (item.duration > 0) startTimer(item.id, item.duration)
  return item.id
}

/**
 * Changes a toast on screen, e.g. a loading toast once its task is done. A new status brings that
 * status's duration unless you pass one; the countdown starts again. Does nothing once it has closed.
 */
function update(id: number, changes: { message?: string } & ToastOptions) {
  const current = toasts.value.find(t => t.id === id)
  if (!current) return
  const status = changes.status ?? current.status
  const next: ToastItem = {
    ...current,
    message: changes.message ?? current.message,
    status,
    duration: changes.duration ?? (changes.status ? defaultDuration(status) : current.duration),
  }
  stopTimer(id)
  toasts.value = toasts.value.map(t => (t.id === id ? next : t))
  if (next.duration > 0) startTimer(id, next.duration)
}

/**
 * One toast for an asynchronous task: loading while it runs, then success or error. Takes the
 * promise, or a function that starts the task, and returns the task's promise.
 */
function promise<T>(task: Promise<T> | (() => Promise<T>), messages: ToastPromiseMessages<T>): Promise<T> {
  const id = show(messages.loading, { status: 'loading' })
  // A task that throws before returning a promise still settles the toast, as a rejection
  const run = Promise.resolve().then(() => (typeof task === 'function' ? task() : task))
  // A message function that throws falls back to plain text, so the toast never stays loading
  const text = <V>(m: ToastMessage<V>, value: V, fallback: string) => {
    try { return typeof m === 'function' ? m(value) : m }
    catch { return fallback }
  }
  run.then(
    value => update(id, { message: text(messages.success, value, 'Done'), status: 'success' }),
    (error: unknown) => update(id, { message: text(messages.error, error, error instanceof Error ? error.message : 'Something went wrong'), status: 'error' }),
  )
  return run
}

const withStatus = (status: ToastStatus) => (message: string, options: Omit<ToastOptions, 'status'> = {}) => show(message, { ...options, status })

/** toast(message, options), with toast.success, .info, .warning, .error, .loading and .promise as shortcuts. */
const toast = Object.assign(show, {
  success: withStatus('success'),
  info: withStatus('info'),
  warning: withStatus('warning'),
  error: withStatus('error'),
  loading: withStatus('loading'),
  promise,
})

/** Show a toast from anywhere: `const { toast } = useToast(); toast('Link copied')`. Render <Toaster /> once in your app. */
export function useToast() {
  return { toasts, toast, dismiss, update, pause, resume }
}
