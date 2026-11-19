// App-wide dialogs. Toasts and upload progress use the library's toast().
import { defineStore } from "pinia";
import { ref } from "vue";

import type { MediaKind } from "@/types";

export type PendingDelete =
  | { kind: "session"; id: string }
  | { kind: MediaKind; media: { id: string; collection_id: string } };

export const useUiStore = defineStore("ui", () => {
  const pendingDelete = ref<PendingDelete | null>(null);
  const showUploadDialog = ref(false);
  const showCreateCollection = ref(false);

  return { pendingDelete, showUploadDialog, showCreateCollection };
});
