<template>
  <form
    class="flex flex-col gap-8 rounded-lg border border-border-neutral-strong bg-background-neutral-primary p-12 shadow-sm transition-colors focus-within:border-border-neutral-field-hover"
    :class="{ 'pointer-events-none opacity-40': disabled }"
    @submit.prevent="submit"
  >
    <div v-if="images.length" class="flex flex-wrap gap-8">
      <AttachmentChip
        v-for="a in images"
        :key="a.key"
        kind="image"
        :name="a.image_data.name"
        :error="a.upload_status === 'error' ? 'Upload failed' : undefined"
        @remove="remove(a.key)"
      />
    </div>

    <textarea
      ref="inputRef"
      v-model="chat.chatInput"
      rows="1"
      :placeholder="placeholder"
      autocomplete="off"
      aria-label="Message"
      class="max-h-[25vh] w-full resize-none bg-transparent px-4 text-md text-text-neutral-primary outline-none placeholder:text-text-neutral-tertiary"
      @input="resize"
      @keydown.enter.exact.prevent="submit"
      @paste="onPaste"
    />

    <div class="flex items-center gap-8">
      <IconButton
        icon="attach_file"
        label="Attach an image"
        hierarchy="tertiary"
        size="sm"
        @click="fileRef?.click()"
      />
      <input ref="fileRef" type="file" accept="image/*" class="hidden" @change="onFile" />
      <div class="ml-auto"><ModePicker /></div>
      <SendButton
        size="sm"
        :ready="canSend"
        :processing="chat.chatLoading"
      />
    </div>
  </form>
</template>

<script setup lang="ts">
import { v4 as uuidv4 } from "uuid";
import { computed, nextTick, ref } from "vue";

import { AttachmentChip } from "@/components/ui/attachment-chip";
import { IconButton } from "@/components/ui/icon-button";
import { SendButton } from "@/components/ui/send-button";
import ModePicker from "./elements/ModePicker.vue";
import { useChatStore } from "@/stores/chat";
import type { ImageAttachment } from "@/types";

withDefaults(defineProps<{ placeholder?: string; disabled?: boolean }>(), {
  placeholder: "Ask Director",
});
const emit = defineEmits<{
  "on-submit": [{ text: string; images: ImageAttachment[] }];
}>();

const chat = useChatStore();
// Reactive array in the store; mutated in place, never reassigned.
const attachments = chat.chatAttachments;
const inputRef = ref<HTMLTextAreaElement | null>(null);
const fileRef = ref<HTMLInputElement | null>(null);

const images = computed(() => attachments.filter((a) => a.type === "image"));
const uploading = computed(() =>
  images.value.some((a) => a.upload_status === "uploading" || a.upload_status === "in_queue"),
);
const canSend = computed(
  () => !chat.chatLoading && chat.chatInput.trim() !== "" && !uploading.value,
);

function resize() {
  const el = inputRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
}

function attach(file: File) {
  // One image per message.
  attachments.splice(0, attachments.length, {
    type: "image",
    key: uuidv4(),
    image_data: file,
    upload: true,
    upload_status: "in_queue",
  });
}

function onFile(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) attach(file);
  input.value = "";
}

function onPaste(e: ClipboardEvent) {
  const item = Array.from(e.clipboardData?.items ?? []).find(
    (i) => i.kind === "file" && i.type.startsWith("image/"),
  );
  const file = item?.getAsFile();
  if (!file) return;
  e.preventDefault();
  attach(file);
}

function remove(key: string) {
  const i = attachments.findIndex((a) => a.key === key);
  if (i !== -1) attachments.splice(i, 1);
}

async function submit() {
  if (!canSend.value) return;
  emit("on-submit", { text: chat.chatInput, images: [...images.value] });
  chat.chatInput = "";
  attachments.splice(0, attachments.length);
  await nextTick();
  resize();
}

defineExpose({ focus: () => inputRef.value?.focus() });
</script>
