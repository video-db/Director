export { default as Kbd } from './Kbd.vue'
export { default as KbdGroup } from './KbdGroup.vue'
export * from './variants'

// Symbols read badly aloud ("command"), so shortcut hints inside menu items are hidden from screen
// readers and exposed through aria-keyshortcuts instead, e.g. ['⌘', 'C'] → "Meta+C".
const keyNames: Record<string, string> = { '⌘': 'Meta', '⌃': 'Control', '⌥': 'Alt', '⇧': 'Shift', '⌫': 'Backspace', '⌦': 'Delete', '⏎': 'Enter', '↵': 'Enter', '⎋': 'Escape', '↑': 'ArrowUp', '↓': 'ArrowDown', '←': 'ArrowLeft', '→': 'ArrowRight' }
export function toAriaKeyshortcuts(keys: string | string[]) {
  return [keys].flat().map(k => keyNames[k] ?? k).join('+')
}
