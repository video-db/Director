<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <form class="flex min-h-0 flex-1 flex-col" @submit.prevent="submit">
        <DialogHeader title="New collection" />
        <DialogBody>
          <Field label="Name" required :error="nameError">
            <Input
              v-model="name"
              placeholder="e.g. Product demos"
              autocomplete="off"
              required
              @update:model-value="nameError = undefined"
            />
          </Field>
          <Field label="Description">
            <Textarea
              v-model="description"
              placeholder="What's in this collection?"
              autocomplete="off"
            />
          </Field>
        </DialogBody>
        <DialogFooter>
          <Button hierarchy="secondary" @click="open = false">Cancel</Button>
          <Button hierarchy="primary" type="submit" :disabled="!name.trim()">Create</Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const open = defineModel<boolean>("open", { default: false });
const emit = defineEmits<{ create: [form: { name: string; description?: string }] }>();

const name = ref("");
const description = ref("");
const nameError = ref<string>();

// Start fresh each time the dialog opens.
watch(open, (isOpen) => {
  if (!isOpen) return;
  name.value = "";
  description.value = "";
  nameError.value = undefined;
});

function submit() {
  const trimmed = name.value.trim();
  if (!trimmed) {
    nameError.value = "Give the collection a name";
    return;
  }
  emit("create", { name: trimmed, description: description.value.trim() || undefined });
}
</script>
