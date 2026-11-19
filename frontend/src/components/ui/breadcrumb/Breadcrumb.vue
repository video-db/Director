<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { BreadcrumbSeparator, BreadcrumbStep } from '.'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import {
  breadcrumbClasses,
  breadcrumbCurrentClasses,
  breadcrumbCurrentIconClasses,
  breadcrumbDotClasses,
  breadcrumbItemClasses,
  breadcrumbLabelClasses,
  breadcrumbLinkClasses,
  breadcrumbListClasses,
  breadcrumbSeparatorClasses,
  breadcrumbSlashClasses,
  breadcrumbTextClasses,
  breadcrumbTriggerClasses,
} from '.'

const props = withDefaults(defineProps<{
  steps: BreadcrumbStep[]
  /** Element used for links, e.g. NuxtLink or RouterLink */
  linkAs?: string | object
  /** What sits between steps */
  separator?: BreadcrumbSeparator
  class?: HTMLAttributes['class']
}>(), {
  linkAs: 'a',
  separator: 'chevron',
})

// Only the prop the link takes: an unset href would reach a router link's <a> and wipe its own
const linkProps = (href: string) => props.linkAs === 'a' ? { href } : { to: href }
</script>

<template>
  <nav data-slot="breadcrumb" aria-label="Breadcrumb" :class="cn(breadcrumbClasses, props.class)">
    <ol :class="breadcrumbListClasses">
      <li v-for="(step, i) in steps" :key="i" :class="breadcrumbItemClasses">
        <template v-if="i > 0">
          <span v-if="separator === 'dot'" aria-hidden="true" :class="breadcrumbDotClasses" />
          <span v-else-if="separator === 'slash'" aria-hidden="true" :class="breadcrumbSlashClasses">/</span>
          <Icon v-else name="chevron_right" :size="20" :class="breadcrumbSeparatorClasses" aria-hidden="true" />
        </template>
        <span
          v-if="i === steps.length - 1"
          aria-current="page"
          :class="breadcrumbCurrentClasses"
        >
          <Icon v-if="step.icon" :name="step.icon" :size="20" :class="breadcrumbCurrentIconClasses" />
          <span :class="breadcrumbLabelClasses">{{ step.label }}</span>
        </span>
        <!-- A step with items opens a menu of links; without a label it's the ellipsis of a collapsed trail -->
        <DropdownMenu v-else-if="step.items?.length">
          <DropdownMenuTrigger :class="breadcrumbTriggerClasses" :aria-label="step.label ? undefined : 'Show hidden steps'">
            <template v-if="step.label">
              <Icon v-if="step.icon" :name="step.icon" :size="20" />
              <span :class="breadcrumbLabelClasses">{{ step.label }}</span>
              <Icon name="keyboard_arrow_down" :size="20" />
            </template>
            <Icon v-else name="more_horiz" :size="20" />
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem v-for="item in step.items" :key="item.href" :as="linkAs" v-bind="linkProps(item.href)">
              {{ item.label }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <!-- A step without an href is plain text: a link with nowhere to go can't be reached by keyboard -->
        <span v-else-if="!step.href" :class="breadcrumbTextClasses">
          <Icon v-if="step.icon" :name="step.icon" :size="20" />
          <span :class="breadcrumbLabelClasses">{{ step.label }}</span>
        </span>
        <component
          :is="linkAs"
          v-else
          v-bind="linkProps(step.href!)"
          :class="breadcrumbLinkClasses"
        >
          <Icon v-if="step.icon" :name="step.icon" :size="20" />
          <span :class="breadcrumbLabelClasses">{{ step.label }}</span>
        </component>
      </li>
    </ol>
  </nav>
</template>
