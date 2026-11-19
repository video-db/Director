<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { ToastStatus } from '.'
import { computed } from 'vue'
import { statusStyles } from '@/components/ui/alert'
import { Icon } from '@/components/ui/icon'
import { IconButton } from '@/components/ui/icon-button'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import { statusPrefix, toastClasses, toastMessageClasses, toastNeutralBoxClasses } from '.'

// Usually shown through useToast() and <Toaster />. neutral has no icon; loading shows a spinner.
const props = withDefaults(defineProps<{
  status?: ToastStatus
  class?: HTMLAttributes['class']
}>(), {
  status: 'neutral',
})

const emit = defineEmits<{ dismiss: [] }>()
const coloured = computed(() => (props.status === 'neutral' || props.status === 'loading' ? undefined : statusStyles[props.status]))
</script>

<template>
  <div
    data-slot="toast"
    :data-status="status"
    :class="cn(toastClasses, coloured?.box ?? toastNeutralBoxClasses, props.class)"
    @keydown.esc="emit('dismiss')"
  >
    <!-- Decorative: the status is read from the hidden prefix -->
    <Spinner v-if="status === 'loading'" decorative />
    <Icon v-else-if="coloured" :name="coloured.glyph" :class="coloured.icon" />
    <span v-if="statusPrefix[status]" class="sr-only">{{ statusPrefix[status] }}</span>
    <p :class="toastMessageClasses">
      <slot />
    </p>
    <IconButton icon="close" label="Dismiss" size="sm" shape="circle" @click="emit('dismiss')" />
  </div>
</template>
