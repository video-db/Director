<template>
  <section
    class="vdb-c-flex vdb-c-h-full vdb-c-w-full vdb-c-overflow-hidden vdb-c-bg-white"
  >
    <Sidebar
      v-if="sidebarConfig.enabled"
      ref="sidebarRef"
      :status="isSetupComplete ? 'active' : 'inactive'"
      :new-session-button-status="
        isSetupComplete && route.name !== 'home' ? 'active' : 'inactive'
      "
      :config="sidebarConfig"
      :show-selected-collection="route.name !== 'chat'"
      :initial-sessions-open="!collections.isFreshUser"
      :initial-explore-agents-open="!collections.isFreshUser"
      :selected-session="chat.sessionId ?? ''"
      :add-dummy-session="route.name === 'home'"
      :selected-collection="collections.activeCollectionId ?? 'default'"
      :agents="agents.agents"
      :sessions="sessions.sessions"
      :collections="collections.collections"
      @create-new-session="router.push({ name: 'home' })"
      @create-collection="ui.showCreateCollection = true"
      @delete-session="ui.pendingDelete = { kind: 'session', id: $event }"
      @delete-collection="deleteCollection"
      @agent-click="handleAgentClick"
      @session-click="
        router.push({ name: 'chat', params: { sessionId: $event } })
      "
      @collection-click="
        router.push({ name: 'collection', params: { collectionId: $event } })
      "
    />

    <main
      class="vdb-c-relative vdb-c-flex vdb-c-h-full vdb-c-flex-1 vdb-c-flex-col vdb-c-justify-between vdb-c-bg-white vdb-c-shadow-2"
    >
      <div
        class="vdb-c-chat-parent vdb-c-relative vdb-c-flex vdb-c-flex-1 vdb-c-items-center vdb-c-justify-center vdb-c-overflow-hidden vdb-c-px-12 md:vdb-c-px-[30px]"
      >
        <section
          ref="scrollRef"
          class="vdb-c-flex vdb-c-h-full vdb-c-max-h-full vdb-c-w-full vdb-c-flex-col vdb-c-items-center vdb-c-overflow-x-auto vdb-c-overflow-y-auto"
          @scroll="isScrolled = ($event.target as HTMLElement).scrollTop > 0"
        >
          <div
            ref="headerRef"
            class="vdb-c-sticky vdb-c-top-0 vdb-c-z-40 vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-justify-center vdb-c-bg-white"
          >
            <Header
              v-if="route.name !== 'setup'"
              :is-sidebar-enabled="sidebarConfig.enabled"
              :collection-name="collections.activeCollection?.name"
              :video-name="videoName ?? undefined"
              :header-state="isHome ? 'primary' : 'secondary'"
              :header-config="headerConfig"
              class="vdb-c-header vdb-c-w-full vdb-c-transition-shadow"
              :class="{
                'vdb-c-pl-16 vdb-c-pr-24 md:vdb-c-pl-32 md:vdb-c-pr-60 2xl:vdb-c-pl-60 2xl:vdb-c-pr-80':
                  isHome,
                'vdb-c-border-b-2 vdb-c-border-roy':
                  route.name === 'collection',
                'header-shadow': isScrolled && route.name === 'chat',
              }"
              @toggle-sidebar="sidebarRef?.toggleSidebar()"
              @upload-button-click="ui.showUploadDialog = true"
              @collection-click="openActiveCollection"
            />
          </div>

          <RouterView />
        </section>
        <UploadNotifications />
      </div>

      <div
        v-if="route.name !== 'not-found'"
        class="vdb-c-chat-input-container vdb-c-transition-all vdb-c-duration-300 vdb-c-ease-in-out"
        :class="{
          'vdb-c-pointer-events-none vdb-c-opacity-20': !isSetupComplete,
        }"
      >
        <ChatInput
          :agents="agents.agents"
          :placeholder="chatInputPlaceholder"
          :context-data="
            collections.activeVideo ?? collections.activeCollection ?? undefined
          "
          @on-submit="send"
          @tag-agent="chat.tagAgent($event.name)"
        />
      </div>
    </main>

    <NotificationCenter />

    <ConfirmModal
      :heading-text="deleteCopy.heading"
      :description-text="deleteCopy.description"
      action-button-text="Delete"
      cancel-button-text="Cancel"
      :show-dialog="!!ui.pendingDelete"
      @cancel-delete="ui.pendingDelete = null"
      @confirm-delete="confirmDelete"
    />

    <CreateCollectionModal
      :show-dialog="ui.showCreateCollection"
      @cancel="ui.showCreateCollection = false"
      @create="createCollection"
    />

    <DeleteCollectionErrorModal
      :is-visible="!!deleteCollectionError"
      @close-modal="deleteCollectionError = null"
    >
      <template #description>
        <div>
          This collection contains
          <span
            v-if="
              ['audios', 'images', 'videos'].includes(deleteCollectionError!)
            "
            >{{ deleteCollectionError }}
          </span>
          <span v-else> media </span>. If you wish to delete this collection,
          kindly
          <span v-if="deleteCollectionError === 'videos'">
            remove all the media individually or</span
          >
          use this
          <a
            class="vdb-c-underline"
            href="https://colab.research.google.com/github/video-db/videodb-cookbook/blob/main/guides/Cleanup.ipynb"
            target="_blank"
          >
            notebook</a
          >
          to cleanup the media first.
        </div>
      </template>
    </DeleteCollectionErrorModal>

    <UploadModal
      :show-upload-dialog="ui.showUploadDialog"
      :default-selected-collection-id="
        collections.activeCollectionId ?? undefined
      "
      :collections="collections.collections"
      @upload="handleUpload"
      @cancel-upload="ui.showUploadDialog = false"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { uploadMedia } from "@/api/collections";
import ChatInput from "@/components/chat/ChatInput.vue";
import Header from "@/components/chat/elements/Header.vue";
import NotificationCenter from "@/components/chat/elements/NotificationCenter.vue";
import Sidebar from "@/components/chat/elements/Sidebar.vue";
import UploadNotifications from "@/components/chat/elements/UploadNotifications.vue";
import CheckIcon from "@/components/icons/Check.vue";
import DeleteIcon from "@/components/icons/Delete3.vue";
import ConfirmModal from "@/components/modals/ConfirmModal.vue";
import CreateCollectionModal from "@/components/modals/CreateCollectionModal.vue";
import DeleteCollectionErrorModal from "@/components/modals/DeleteCollectionErrorModal.vue";
import UploadModal from "@/components/modals/UploadModal.vue";
import { useChatActions } from "@/composables/useChatActions";
import { chatInputPlaceholder, headerConfig, sidebarConfig } from "@/config";
import { useAgentsStore } from "@/stores/agents";
import { useChatStore } from "@/stores/chat";
import { useCollectionsStore } from "@/stores/collections";
import { useSessionsStore } from "@/stores/sessions";
import { useUiStore } from "@/stores/ui";
import type { Agent, Collection, UploadRequest } from "@/types";

const route = useRoute();
const router = useRouter();
const agents = useAgentsStore();
const chat = useChatStore();
const collections = useCollectionsStore();
const sessions = useSessionsStore();
const ui = useUiStore();
const { send } = useChatActions();

const sidebarRef = ref<InstanceType<typeof Sidebar> | null>(null);
const scrollRef = ref<HTMLElement | null>(null);
const headerRef = ref<HTMLElement | null>(null);
const isScrolled = ref(false);
const deleteCollectionError = ref<string | null>(null);

const isSetupComplete = computed(() => agents.isSetupComplete);
const isHome = computed(() => route.name === "home");
const videoName = computed(() =>
  route.name === "video" || route.name === "chat"
    ? (collections.activeVideo?.name ?? null)
    : null,
);

// Load app data once the backend is ready.
watch(
  isSetupComplete,
  (ready) => {
    if (!ready) return;
    chat.connect();
    collections.load();
    sessions.load();
    agents.loadAgents();
  },
  { immediate: true },
);

// The video the chat is about drives the header and composer context.
watch(
  () => [collections.activeCollectionId, chat.videoId] as const,
  ([collectionId, videoId]) => {
    if (collectionId) collections.focusVideo(collectionId, videoId);
  },
);

// Keeps `.last-conv-height` below the sticky header.
const headerObserver = new ResizeObserver(([entry]) => {
  document.documentElement.style.setProperty(
    "--header-height",
    `${entry.contentRect.height}px`,
  );
});
watch(headerRef, (el, old) => {
  if (old) headerObserver.unobserve(old);
  if (el) headerObserver.observe(el);
});
onUnmounted(() => headerObserver.disconnect());

function scrollToBottom() {
  nextTick(() => {
    const el = scrollRef.value;
    el?.scroll({ top: el.scrollHeight - 50, behavior: "smooth" });
  });
}
watch(
  () => chat.chatLoading,
  (loading) => loading && scrollToBottom(),
);
watch(
  () => chat.sessionLoading,
  (loading) => !loading && scrollToBottom(),
);

function handleAgentClick(agent: Agent) {
  if (chat.chatLoading) return;
  chat.tagAgent(agent.name);
  send({ text: `@${agent.name} ` });
}

function openActiveCollection() {
  if (!collections.activeCollectionId) return;
  router.push({
    name: "collection",
    params: { collectionId: collections.activeCollectionId },
  });
}

// --- Deletes ---
const deleteCopy = computed(() => {
  const kind = ui.pendingDelete?.kind;
  if (kind === "session") {
    return {
      heading: "Delete Session",
      description: "Are you sure you want to delete this session?",
    };
  }
  const label = kind ? kind[0].toUpperCase() + kind.slice(1) : "";
  return {
    heading: `Delete ${label}`,
    description: `Are you sure you want to delete this ${kind}? This action cannot be undone.`,
  };
});

async function confirmDelete() {
  const pending = ui.pendingDelete;
  ui.pendingDelete = null;
  if (!pending) return;

  if (pending.kind === "session") {
    if (pending.id === chat.sessionId) router.push({ name: "home" });
    sessions.remove(pending.id).catch(() => {
      ui.notify("Error deleting session", { type: "error", icon: DeleteIcon });
    });
    return;
  }

  const label = pending.kind[0].toUpperCase() + pending.kind.slice(1);
  try {
    await collections.deleteMedia(pending.kind, pending.media);
    ui.notify(`${label} deleted successfully.`, {
      type: "error",
      icon: DeleteIcon,
    });
  } catch {
    ui.notify(`Error deleting ${pending.kind}`, {
      type: "error",
      icon: DeleteIcon,
    });
  }
}

async function deleteCollection(collection: Collection) {
  try {
    await collections.remove(collection.id);
    ui.notify("Collection deleted successfully.", {
      type: "error",
      icon: DeleteIcon,
    });
    if (route.params.collectionId === collection.id) {
      router.push({ name: "home" });
    }
  } catch (error) {
    const message = (error as Error).message;
    const match = message.match(/non-zero (videos|audios|images)/);
    if (message.includes("Your collection has non-zero")) {
      deleteCollectionError.value = match?.[1] ?? "media";
      return;
    }
    ui.notify("Failed to delete collection", { type: "error" });
  }
}

async function createCollection(form: { name: string; description?: string }) {
  ui.showCreateCollection = false;
  try {
    await collections.create(form.name, form.description || " ");
    ui.notify("Collection has been created successfully!", {
      type: "success",
      icon: CheckIcon,
    });
  } catch {
    ui.notify("Failed to create collection", { type: "error" });
  }
}

async function handleUpload(upload: UploadRequest) {
  ui.showUploadDialog = false;
  const name =
    upload.sourceType === "file"
      ? (upload.source as File).name
      : (upload.source as { url: string }).url;
  const id = ui.startUpload(name);
  try {
    await uploadMedia(upload);
    ui.finishUpload(id, "success");
    if (upload.collectionId === collections.activeCollectionId) {
      collections.refetchAll();
    }
  } catch {
    ui.finishUpload(id, "error");
  }
}
</script>

<style>
.header-shadow {
  box-shadow:
    0 12px 26px rgba(0, 0, 0, 0.06),
    0 47px 47px rgba(0, 0, 0, 0.05),
    0 105px 63px rgba(0, 0, 0, 0.03),
    0 186px 75px rgba(0, 0, 0, 0.01),
    0 291px 82px rgba(0, 0, 0, 0);
}

.vdb-c-message-container::-webkit-scrollbar {
  width: 8px;
}
.vdb-c-message-container::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}
.vdb-c-message-container::-webkit-scrollbar-thumb:hover {
  background: #aaa;
}

.last-conv-height {
  min-height: calc(100% - var(--header-height));
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
.vdb-c-rotating {
  animation: rotating 2s linear infinite;
}
</style>
