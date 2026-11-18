export const codeBlockClasses = [
  'flex w-full min-w-0 flex-col overflow-hidden rounded-sm border border-border-neutral-primary bg-background-neutral-primary',
  'has-[[data-slot=code-block-content]:focus-visible]:shadow-focus-ring',
]

/** Header: 2px right padding puts the 16px copy icon 12px from the edge. */
export const codeBlockHeaderClasses = 'flex h-40 shrink-0 items-center gap-8 border-b border-border-neutral-primary bg-background-neutral-subtle pr-2 pl-12 text-xs font-medium text-text-neutral-tertiary'
export const codeBlockTitleClasses = 'min-w-0 flex-1 truncate'
export const codeBlockLanguageClasses = 'shrink-0'

/** The copy button's icon colour per copy state. */
export const codeBlockCopyClasses = {
  idle: '',
  copied: 'text-icon-success-primary',
  failed: 'text-icon-error-primary',
} as const

export const codeBlockContentClasses = 'overflow-auto outline-none'
export const codeBlockPreClasses = 'p-12 font-mono text-xs font-medium text-text-neutral-primary'
/** Long lines wrap, or the pre grows so they scroll sideways. */
export const codeBlockPreWrapClasses = { wrap: 'whitespace-pre-wrap wrap-anywhere', scroll: 'w-max min-w-full whitespace-pre' } as const

// Line numbers: a table, so wrapped lines keep their number in its own column.
export const codeBlockLinesClasses = 'table w-full'
export const codeBlockLineClasses = 'table-row'
export const codeBlockLineNumberClasses = 'table-cell w-px pr-16 text-right text-text-neutral-tertiary tabular-nums select-none'
export const codeBlockLineTextClasses = 'table-cell'
