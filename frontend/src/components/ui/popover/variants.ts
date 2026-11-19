import { floatingAnimationClasses, floatingPanelClasses } from '@/lib/floating'

// The panel: the shared floating surface, 240 wide at least, 12 padding. Each framework adds its
// primitive's transform origin, e.g. origin-(--reka-popover-content-transform-origin).
export const popoverContentClasses = [floatingPanelClasses, 'min-w-240 p-12 text-sm text-text-neutral-primary', floatingAnimationClasses]

// A title and description at the top of the panel, 4 apart; whatever follows sits 16 below (gap on a wrapper).
export const popoverHeaderClasses = 'flex flex-col gap-4'
export const popoverTitleClasses = 'font-medium text-text-neutral-primary'
export const popoverDescriptionClasses = 'text-text-neutral-tertiary'
