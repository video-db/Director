// App-wide dialogs, toasts and upload progress.
import { defineStore } from "pinia";
import { markRaw, ref, type Component } from "vue";

import type { MediaKind } from "@/types";

export interface Toast {
  id: number;
  message: string;
  type: "success" | "error";
  icon: Component | null;
}

export interface UploadProgress {
  id: number;
  name: string;
  description: string | null;
  status: "loading" | "success" | "error";
}

export type PendingDelete =
  | { kind: "session"; id: string }
  | { kind: MediaKind; media: { id: string; collection_id: string } };

let nextId = 0;

export const useUiStore = defineStore("ui", () => {
  const toasts = ref<Toast[]>([]);
  const uploads = ref<UploadProgress[]>([]);
  const pendingDelete = ref<PendingDelete | null>(null);
  const showUploadDialog = ref(false);
  const showCreateCollection = ref(false);

  function notify(
    message: string,
    {
      type = "success",
      icon = null,
      duration = 5000,
    }: {
      type?: Toast["type"];
      icon?: Component | null;
      duration?: number;
    } = {},
  ) {
    const id = nextId++;
    toasts.value.push({ id, message, type, icon: icon && markRaw(icon) });
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id);
    }, duration);
  }

  function startUpload(name: string, description: string | null = null) {
    const id = nextId++;
    uploads.value.push({ id, name, description, status: "loading" });
    return id;
  }

  function finishUpload(id: number, status: "success" | "error") {
    const upload = uploads.value.find((u) => u.id === id);
    if (!upload) return;
    upload.status = status;
    setTimeout(
      () => {
        uploads.value = uploads.value.filter((u) => u.id !== id);
      },
      status === "success" ? 3000 : 5000,
    );
  }

  return {
    toasts,
    uploads,
    pendingDelete,
    showUploadDialog,
    showCreateCollection,
    notify,
    startUpload,
    finishUpload,
  };
});
