<script setup lang="ts">
import { AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogOverlay, AlertDialogPortal, AlertDialogRoot, AlertDialogTitle } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { computed, ref, useId, watch } from 'vue'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { DialogFooter, headerRowClasses, headerRowNoTabsClasses, headerTitleClasses, overlayClasses, panelClasses } from '@/components/ui/dialog'
import { Field } from '@/components/ui/field'
import { Icon } from '@/components/ui/icon'
import { IconButton } from '@/components/ui/icon-button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import type { ConfirmationDialogSize } from '.'
import {
  confirmationBodyClasses,
  confirmationBodyXsClasses,
  confirmationDescriptionClasses,
  confirmationFooterXsClasses,
  confirmationMediaClasses,
  confirmationMediaTones,
  confirmationSizes,
  confirmationTextClasses,
  confirmationTitleClasses,
  confirmationTypedBodyClasses,
  confirmationTypedConfirmClasses,
} from '.'

// simple: question + Cancel / Confirm. typed (set confirmText): the user must type confirmText first.
// The root renders no element, so class and other attributes go on the panel.
defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  /** Red confirm button (and a red icon tile). Turn off for non-destructive confirmations. */
  destructive?: boolean
  /** sm: 500 wide, left-aligned. xs: 320 wide, centred, with Cancel and Confirm side by side at equal width. */
  size?: ConfirmationDialogSize
  /** Material Symbols name for an icon tile beside the heading (above it at xs) */
  icon?: string
  /** Material Symbols name on the confirm button */
  confirmIcon?: string
  /** When set, the user must type this text exactly before confirming */
  confirmText?: string
  /** Shows a spinner on the confirm button */
  loading?: boolean
  /** Set to false for async work: the dialog stays open after "confirm" until you set open to false */
  closeOnConfirm?: boolean
  class?: HTMLAttributes['class']
}>(), {
  confirmLabel: 'Yes, I\'m sure',
  cancelLabel: 'Cancel',
  destructive: true,
  size: 'sm',
  closeOnConfirm: true,
})

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ confirm: [] }>()

const typed = ref('')
const inputId = useId()
const inputRef = ref<InstanceType<typeof Input>>()
const canConfirm = computed(() => !props.confirmText || typed.value.trim() === props.confirmText)
watch(open, (v) => { if (v) typed.value = '' })

// Typed variant: start in the input, since typing is the next step.
function onOpenAutoFocus(e: Event) {
  if (!props.confirmText) return
  e.preventDefault()
  inputRef.value?.focus()
}

function confirm() {
  if (!canConfirm.value || props.loading) return
  emit('confirm')
  if (props.closeOnConfirm) open.value = false
}
</script>

<template>
  <AlertDialogRoot v-model:open="open">
    <slot name="trigger" />
    <AlertDialogPortal>
      <AlertDialogOverlay :class="overlayClasses" />
      <AlertDialogContent
        data-slot="confirmation-dialog"
        v-bind="$attrs"
        :class="cn(panelClasses, confirmationSizes[size], props.class)"
        @open-auto-focus="onOpenAutoFocus"
      >
        <!-- typed: modal header with a close button -->
        <template v-if="confirmText">
          <div :class="[headerRowClasses, headerRowNoTabsClasses]">
            <AlertDialogTitle :class="headerTitleClasses">
              {{ title }}
            </AlertDialogTitle>
            <!-- Not an AlertDialogCancel: that would take initial focus away from the input -->
            <IconButton icon="close" :label="cancelLabel" shape="circle" @click="open = false" />
          </div>
          <div :class="confirmationTypedBodyClasses">
            <!-- Not live: the alertdialog already reads the description when it opens -->
            <Alert status="warning">
              <AlertDialogDescription>{{ description }}</AlertDialogDescription>
            </Alert>
            <Field :for="inputId" :label="`To confirm, type “${confirmText}” in the box below`">
              <Input :id="inputId" ref="inputRef" v-model="typed" autocomplete="off" spellcheck="false" @keydown.enter.prevent="canConfirm && confirm()" />
            </Field>
          </div>
        </template>

        <!-- simple: heading and detail -->
        <div v-else :class="cn(confirmationBodyClasses, size === 'xs' && confirmationBodyXsClasses)">
          <div v-if="icon" :class="cn(confirmationMediaClasses, confirmationMediaTones[destructive ? 'destructive' : 'neutral'])">
            <Icon :name="icon" :size="24" />
          </div>
          <div :class="confirmationTextClasses">
            <AlertDialogTitle :class="confirmationTitleClasses">
              {{ title }}
            </AlertDialogTitle>
            <AlertDialogDescription :class="confirmationDescriptionClasses">
              {{ description }}
            </AlertDialogDescription>
          </div>
        </div>

        <DialogFooter :class="size === 'xs' && !confirmText && confirmationFooterXsClasses">
          <AlertDialogCancel v-if="!confirmText" as-child>
            <Button hierarchy="secondary">{{ cancelLabel }}</Button>
          </AlertDialogCancel>
          <!-- A plain button, so the dialog can stay open while async work runs -->
          <Button
            :destructive="destructive"
            :icon="confirmIcon"
            :loading="loading"
            :disabled="!canConfirm"
            :class="confirmText && confirmationTypedConfirmClasses"
            @click="confirm"
          >
            {{ confirmLabel }}
          </Button>
        </DialogFooter>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>
