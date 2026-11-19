<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { PaginationEllipsis, PaginationList, PaginationListItem, PaginationNext, PaginationPrev, PaginationRoot } from 'reka-ui'
import { watch } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import type { PaginationLayout } from './variants'
import { paginationClasses, paginationEllipsisClasses, paginationListClasses, paginationNextIconClasses, paginationPageClasses, paginationPagesClasses, paginationPrevIconClasses, paginationStepClasses } from './variants'

const props = withDefaults(defineProps<{
  /** Total number of items */
  total: number
  itemsPerPage?: number
  /** Pages shown either side of the current one */
  siblingCount?: number
  /** full: Previous, the page numbers and Next · pages: the page numbers only · arrows: Previous and Next only */
  layout?: PaginationLayout
  /** Accessible name for the navigation landmark; make it specific when a page has more than one */
  label?: string
  class?: HTMLAttributes['class']
}>(), {
  itemsPerPage: 10,
  siblingCount: 1,
  layout: 'full',
  label: 'Pagination',
})

const page = defineModel<number>('page', { default: 1 })

// The page buttons are keyed by position, so after a page change focus would stay in its slot, which
// now holds another page; and an arrow that becomes disabled on the first or last page drops focus to
// the body. So after a page change made here, focus moves to the current page, unless it's on an arrow
// that still works (with no page numbers, the other arrow). Focus elsewhere on the screen is left alone.
let pressedIn: HTMLElement | undefined
const onPress = (e: MouseEvent) => {
  pressedIn = e.currentTarget as HTMLElement
  // A press that changed nothing (the current page, a gap) is forgotten once the click is handled, so a
  // later change made from code leaves focus alone, as in React
  setTimeout(() => { pressedIn = undefined })
}
watch(page, () => {
  const nav = pressedIn
  pressedIn = undefined
  if (!nav) return
  const active = document.activeElement as HTMLElement | null
  const inPagination = !!active && nav.contains(active)
  const lost = !active || active === document.body
  if (!lost && !(inPagination && (active.dataset.type === 'page' || active.matches(':disabled')))) return
  const target = nav.querySelector<HTMLElement>('[aria-current="page"]') ?? nav.querySelector<HTMLElement>('button:not(:disabled)')
  target?.focus()
}, { flush: 'post' })
</script>

<template>
  <PaginationRoot
    v-model:page="page"
    data-slot="pagination"
    :total="total"
    :items-per-page="itemsPerPage"
    :sibling-count="siblingCount"
    show-edges
    :aria-label="label"
    :class="cn(paginationClasses, props.class)"
    @click.capture="onPress"
  >
    <PaginationList v-slot="{ items }" :class="paginationListClasses">
      <PaginationPrev v-if="layout !== 'pages'" :class="cn(paginationStepClasses, 'group/prev')">
        <Icon name="arrow_back" :class="paginationPrevIconClasses" />
        Previous
      </PaginationPrev>
      <div v-if="layout !== 'arrows'" :class="paginationPagesClasses">
        <template v-for="(item, i) in items" :key="i">
          <PaginationListItem
            v-if="item.type === 'page'"
            :value="item.value"
            :class="paginationPageClasses"
          >
            {{ item.value }}
          </PaginationListItem>
          <PaginationEllipsis v-else :index="i" aria-hidden="true" :class="paginationEllipsisClasses">
            …
          </PaginationEllipsis>
        </template>
      </div>
      <PaginationNext v-if="layout !== 'pages'" :class="cn(paginationStepClasses, 'group/next')">
        Next
        <Icon name="arrow_forward" :class="paginationNextIconClasses" />
      </PaginationNext>
    </PaginationList>
  </PaginationRoot>
</template>
