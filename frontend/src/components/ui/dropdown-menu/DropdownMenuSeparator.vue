<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { DropdownMenuSeparator } from 'reka-ui'
import { separatorClasses } from '@/lib/floating'
import { cn } from '@/lib/utils'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <DropdownMenuSeparator data-slot="dropdown-menu-separator" :class="cn(separatorClasses, props.class)" />
</template>
