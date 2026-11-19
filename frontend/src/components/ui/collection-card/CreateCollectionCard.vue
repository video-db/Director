<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Icon } from '@/components/ui/icon'
import { cn } from '@/lib/utils'
import { createCollectionCardClasses, createCollectionCardIconBoxClasses, createCollectionCardIconClasses, createCollectionCardLabelClasses } from '.'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <button
    data-slot="create-collection-card"
    type="button"
    :class="cn(createCollectionCardClasses, props.class)"
  >
    <span :class="createCollectionCardIconBoxClasses">
      <Icon name="create_new_folder" :size="24" :class="createCollectionCardIconClasses" />
    </span>
    <span :class="createCollectionCardLabelClasses">
      <slot>Create new collection</slot>
    </span>
  </button>
</template>
