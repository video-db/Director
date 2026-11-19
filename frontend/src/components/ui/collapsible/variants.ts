// The only styling is the open/close height animation, keyed on data-state="open" | "closed" (as Reka UI
// marks it; the React panel sets it too). The height comes from --reka-collapsible-content-height, which
// the React panel maps from Base UI's --collapsible-panel-height.
export const collapsibleContentClasses = 'overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down'

// React: Base UI unmounts a closed panel a frame after its close animation ends, so the panel would show
// at full height for that frame. It marks the panel data-ending-style while closing; hold it at 0.
export const collapsibleContentEndingClasses = 'data-ending-style:h-0'
