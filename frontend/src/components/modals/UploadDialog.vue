<template>
  <Dialog v-model:open="open">
    <DialogContent size="lg">
      <Tabs v-model="source" class="min-h-0 flex-1 gap-0">
        <DialogHeader title="Upload media">
          <template #tabs>
            <TabsList variant="line" aria-label="Upload from">
              <TabsTrigger value="file" icon="upload_file">File</TabsTrigger>
              <TabsTrigger value="url" icon="link">Link</TabsTrigger>
            </TabsList>
          </template>
        </DialogHeader>

        <DialogBody>
          <template v-if="source === 'file'">
            <div class="flex flex-col gap-8">
              <UploadDropzone
                title="Select files or drag and drop here"
                description="Video, audio and image files"
                :accept="ACCEPT"
                :error="fileError"
                @files="addFiles"
              />
              <div
                v-if="files.length"
                class="flex max-h-240 flex-col gap-8 overflow-y-auto rounded-sm bg-background-neutral-secondary p-8"
              >
                <AttachmentChip
                  v-for="(file, index) in files"
                  :key="`${file.name}-${file.lastModified}-${index}`"
                  class="w-full"
                  :name="file.name"
                  :kind="kindOf(file)"
                  :size="file.size"
                  @remove="files.splice(index, 1)"
                />
              </div>
            </div>
          </template>

          <Field v-else label="Media URL" required :error="urlError">
            <Input
              v-model="url"
              type="url"
              leading-icon="link"
              placeholder="https://www.youtube.com/watch?v=…"
              autocomplete="off"
              clearable
              @update:model-value="urlError = undefined"
            />
          </Field>

          <Field label="Add to collection" required :error="collectionError">
            <Select v-model="collectionId" @update:model-value="collectionError = undefined">
              <SelectTrigger leading-icon="folder">
                <SelectValue placeholder="Select a collection" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="c in collections" :key="c.id" :value="c.id">
                  {{ c.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </Field>
        </DialogBody>
      </Tabs>

      <DialogFooter>
        <Button hierarchy="secondary" @click="open = false">Cancel</Button>
        <Button hierarchy="primary" icon="upload" :disabled="!canUpload" @click="submit">
          {{ uploadLabel }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { AttachmentChip } from "@/components/ui/attachment-chip";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UploadDropzone } from "@/components/ui/upload-dropzone";
import type { Collection, UploadRequest } from "@/types";

const ACCEPT = "audio/*,video/*,image/*";

const props = defineProps<{
  collections: Collection[];
  defaultCollectionId?: string;
}>();
const open = defineModel<boolean>("open", { default: false });
const emit = defineEmits<{ upload: [upload: UploadRequest] }>();

const source = ref<"file" | "url">("file");
const files = ref<File[]>([]);
const url = ref("");
const collectionId = ref<string>();
const fileError = ref<string>();
const urlError = ref<string>();
const collectionError = ref<string>();

const canUpload = computed(() =>
  source.value === "file" ? files.value.length > 0 : !!url.value.trim(),
);
const uploadLabel = computed(() =>
  source.value === "file" && files.value.length > 1
    ? `Upload ${files.value.length} files`
    : "Upload",
);

function pickDefaultCollection() {
  const ids = props.collections.map((c) => c.id);
  if (props.defaultCollectionId && ids.includes(props.defaultCollectionId)) {
    collectionId.value = props.defaultCollectionId;
  } else if (!collectionId.value || !ids.includes(collectionId.value)) {
    collectionId.value = ids[0];
  }
}

// Each open starts clean, targeting the active collection (or the first one).
watch(open, (isOpen) => {
  if (!isOpen) return;
  source.value = "file";
  files.value = [];
  url.value = "";
  fileError.value = urlError.value = collectionError.value = undefined;
  collectionId.value = undefined;
  pickDefaultCollection();
});

// Collections may load after the dialog is mounted.
watch(
  () => [props.collections, props.defaultCollectionId] as const,
  () => {
    if (open.value && collectionId.value) return;
    pickDefaultCollection();
  },
  { immediate: true },
);

function kindOf(file: File): "video" | "audio" | "image" | "file" {
  const type = file.type.split("/")[0];
  return type === "video" || type === "audio" || type === "image" ? type : "file";
}

function addFiles(picked: File[]) {
  fileError.value = undefined;
  files.value = [...files.value, ...picked];
}

function isHttpUrl(value: string) {
  try {
    return ["http:", "https:"].includes(new URL(value).protocol);
  } catch {
    return false;
  }
}

function submit() {
  if (!collectionId.value) {
    collectionError.value = "Pick a collection to upload to";
    return;
  }
  const target = collectionId.value;

  if (source.value === "url") {
    const value = url.value.trim();
    if (!isHttpUrl(value)) {
      urlError.value = "Enter a valid http(s) URL";
      return;
    }
    emit("upload", { collectionId: target, sourceType: "url", source: { url: value } });
    return;
  }

  if (!files.value.length) {
    fileError.value = "Add at least one file";
    return;
  }
  // One upload per file, as before.
  for (const file of files.value) {
    emit("upload", { collectionId: target, sourceType: "file", source: file });
  }
}
</script>
