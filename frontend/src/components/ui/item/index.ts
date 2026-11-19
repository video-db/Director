import type { InjectionKey } from 'vue'

export { default as Item } from './Item.vue'
export { default as ItemActions } from './ItemActions.vue'
export { default as ItemContent } from './ItemContent.vue'
export { default as ItemDescription } from './ItemDescription.vue'
export { default as ItemGroup } from './ItemGroup.vue'
export { default as ItemMedia } from './ItemMedia.vue'
export { default as ItemSeparator } from './ItemSeparator.vue'
export { default as ItemTitle } from './ItemTitle.vue'
export * from './variants'

// Set by ItemGroup, so items and separators inside it take list semantics.
export const itemGroupKey: InjectionKey<true> = Symbol('item-group')
