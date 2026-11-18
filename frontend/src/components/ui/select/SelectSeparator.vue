<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { SelectSeparator } from 'reka-ui'
import { separatorClasses } from '@/lib/floating'
import { cn } from '@/lib/utils'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <SelectSeparator data-slot="select-separator" :class="cn(separatorClasses, props.class)" />
</template>
