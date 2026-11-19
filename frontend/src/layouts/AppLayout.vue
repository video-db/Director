<template>
  <SidebarProvider class="h-dvh">
    <AppSidebar :ready="ready" @delete-collection="deleteCollection" />

    <SidebarInset class="flex h-dvh min-w-0 flex-col overflow-hidden">
      <AppHeader v-if="route.name !== 'setup'" :ready="ready" />

      <!-- min-w-0: flex items can't shrink below their widest content otherwise,
           so a long code line would widen the page instead of scrolling. -->
      <div
        class="relative min-h-0 min-w-0 flex-1"
        :class="route.name === 'chat' ? 'flex flex-col' : 'overflow-y-auto'"
      >
        <RouterView />
      </div>

      <div
        v-if="!['not-found', 'setup', 'skills'].includes(String(route.name))"
        class="shrink-0 px-16 pb-16 pt-8 md:px-24"
      >
        <ChatInput
          class="mx-auto max-w-760"
          :placeholder="chatInputPlaceholder"
          :disabled="!ready"
          @on-submit="send"
        />
      </div>
    </SidebarInset>

    <ConfirmationDialog
      :open="!!ui.pendingDelete"
      :title="deleteCopy.title"
      :description="deleteCopy.description"
      confirm-label="Delete"
      confirm-icon="delete"
      @update:open="(v) => !v && (ui.pendingDelete = null)"
      @confirm="confirmDelete"
    />

    <CreateCollectionDialog
      v-model:open="ui.showCreateCollection"
      @create="createCollection"
    />

    <Dialog :open="!!notEmptyKind" @update:open="(v) => !v && (notEmptyKind = null)">
      <DialogContent>
        <DialogHeader title="This collection isn't empty" />
        <DialogBody>
          <p class="text-sm text-text-neutral-secondary">
            It still has {{ notEmptyKind }}. Remove them first<template v-if="notEmptyKind === 'videos'">, one at a time or</template>
            with the
            <a
              class="font-medium text-text-brand-primary underline underline-offset-2"
              href="https://colab.research.google.com/github/video-db/videodb-cookbook/blob/main/guides/Cleanup.ipynb"
              target="_blank"
              rel="noopener noreferrer"
              >cleanup notebook</a
            >, then delete the collection.
          </p>
        </DialogBody>
        <DialogFooter>
          <Button hierarchy="primary" @click="notEmptyKind = null">Got it</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <PermissionRulesDialog v-model:open="ui.showPermissionRules" />

    <UploadDialog
      v-model:open="ui.showUploadDialog"
      :collections="collections.collections"
      :default-collection-id="collections.activeCollectionId ?? undefined"
      @upload="handleUpload"
    />

    <Toaster />
  </SidebarProvider>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { uploadMedia } from "@/api/collections";
import ChatInput from "@/components/chat/ChatInput.vue";
import AppHeader from "@/components/layout/AppHeader.vue";
import AppSidebar from "@/components/layout/AppSidebar.vue";
import CreateCollectionDialog from "@/components/modals/CreateCollectionDialog.vue";
import PermissionRulesDialog from "@/components/modals/PermissionRulesDialog.vue";
import UploadDialog from "@/components/modals/UploadDialog.vue";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components/ui/dialog";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Toaster, useToast } from "@/components/ui/toast";
import { useChatActions } from "@/composables/useChatActions";
import { chatInputPlaceholder } from "@/config";
import { useChatStore } from "@/stores/chat";
import { useConfigStore } from "@/stores/config";
import { useCollectionsStore } from "@/stores/collections";
import { useSessionsStore } from "@/stores/sessions";
import { useUiStore } from "@/stores/ui";
import type { Collection, UploadRequest } from "@/types";

const route = useRoute();
const router = useRouter();
const chat = useChatStore();
const config = useConfigStore();
const collections = useCollectionsStore();
const sessions = useSessionsStore();
const ui = useUiStore();
const { toast } = useToast();
const { send } = useChatActions();

const ready = computed(() => config.isSetupComplete);
const notEmptyKind = ref<string | null>(null);

// Load app data once the backend is ready.
watch(
  ready,
  (isReady) => {
    if (!isReady) return;
    chat.connect();
    collections.load();
    sessions.load();
    config.loadPermissions();
  },
  { immediate: true },
);

watch(
  () => config.permissions,
  (permissions) => permissions && chat.applyPermissions(permissions),
);

// The video the chat is about drives the header and composer context.
watch(
  () => [collections.activeCollectionId, chat.videoId] as const,
  ([collectionId, videoId]) => {
    if (collectionId) collections.focusVideo(collectionId, videoId);
  },
);

// --- Deletes ---
const deleteCopy = computed(() => {
  const kind = ui.pendingDelete?.kind;
  if (kind === "session") {
    return { title: "Delete this chat?", description: "The chat and its messages are removed for good." };
  }
  return {
    title: `Delete this ${kind ?? "item"}?`,
    description: `The ${kind ?? "item"} is removed from the collection. This can't be undone.`,
  };
});

async function confirmDelete() {
  const pending = ui.pendingDelete;
  ui.pendingDelete = null;
  if (!pending) return;

  if (pending.kind === "session") {
    if (pending.id === chat.sessionId) router.push({ name: "home" });
    sessions.remove(pending.id).catch(() => toast.error("Couldn't delete the chat"));
    return;
  }

  try {
    await collections.deleteMedia(pending.kind, pending.media);
    toast.success(`Deleted the ${pending.kind}`);
  } catch {
    toast.error(`Couldn't delete the ${pending.kind}`);
  }
}

async function deleteCollection(collection: Collection) {
  try {
    await collections.remove(collection.id);
    toast.success(`Deleted ${collection.name}`);
    if (route.params.collectionId === collection.id) router.push({ name: "home" });
  } catch (error) {
    const message = (error as Error).message;
    if (message.includes("Your collection has non-zero")) {
      notEmptyKind.value = message.match(/non-zero (videos|audios|images)/)?.[1] ?? "media";
      return;
    }
    toast.error("Couldn't delete the collection");
  }
}

async function createCollection(form: { name: string; description?: string }) {
  ui.showCreateCollection = false;
  try {
    await collections.create(form.name, form.description || " ");
    toast.success(`Created ${form.name}`);
  } catch {
    toast.error("Couldn't create the collection");
  }
}

function handleUpload(upload: UploadRequest) {
  ui.showUploadDialog = false;
  const name =
    upload.sourceType === "file"
      ? (upload.source as File).name
      : (upload.source as { url: string }).url;
  toast
    .promise(uploadMedia(upload), {
      loading: `Uploading ${name}`,
      success: `Uploaded ${name}`,
      error: `Couldn't upload ${name}`,
    })
    .then(() => {
      if (upload.collectionId === collections.activeCollectionId) collections.refetchAll();
    })
    .catch(() => {});
}
</script>
