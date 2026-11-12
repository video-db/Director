// The open session: its conversations, the composer, and the /chat socket handlers.
import { defineStore } from "pinia";
import { v4 as uuidv4 } from "uuid";
import { computed, reactive, ref, watch } from "vue";

import * as collectionsApi from "@/api/collections";
import { getSession } from "@/api/sessions";
import { useChatSocket } from "@/composables/useChatSocket";
import type {
  ContentBase,
  Conversations,
  ImageAttachment,
  Message,
} from "@/types";
import { useCollectionsStore } from "./collections";
import { useSessionsStore } from "./sessions";

export const useChatStore = defineStore("chat", () => {
  const collections = useCollectionsStore();
  const sessions = useSessionsStore();

  const sessionId = ref<string | null>(null);
  // Video the next message is about; sent as video_id.
  const videoId = ref<string | null>(null);
  const conversations = reactive<Conversations>({});
  const sessionLoading = ref(false);

  const chatInput = ref("");
  const chatAttachments = reactive<ImageAttachment[]>([]);

  const chatLoading = computed(() =>
    Object.values(conversations).some((conv) =>
      Object.values(conv).some(
        (msg) => msg.status === "progress" || msg.clientLoading,
      ),
    ),
  );

  const isEmpty = computed(() => Object.keys(conversations).length === 0);

  function clearConversations() {
    for (const key of Object.keys(conversations)) delete conversations[key];
  }

  // Leave the current session, e.g. when going home or to a collection.
  function reset() {
    sessionId.value = null;
    videoId.value = null;
    clearConversations();
  }

  function startNewSession() {
    const id: string = uuidv4();
    sessionId.value = id;
    clearConversations();
    return id;
  }

  async function openSession(id: string) {
    if (id === sessionId.value) return;
    sessionId.value = id;
    clearConversations();
    sessionLoading.value = true;
    try {
      const data = await getSession(id);
      if (sessionId.value !== id) return;
      videoId.value = data.video_id || null;
      if (data.collection_id) collections.setActive(data.collection_id);
      for (const message of data.conversation ?? []) {
        const convId = String(message.conv_id);
        conversations[convId] ??= {};
        conversations[convId][String(message.msg_id)] = {
          ...message,
          sender: message.msg_type === "input" ? "user" : "assistant",
        };
      }
    } catch {
      // Unknown or never-sent session: show it empty.
    } finally {
      if (sessionId.value === id) sessionLoading.value = false;
    }
  }

  function addMessage(content: ContentBase[]) {
    const id = sessionId.value ?? startNewSession();
    sessions.track(id);
    const convId = String(Date.now());
    const msgId = String(Date.now() + 1);
    const message: Message = {
      msg_type: "input",
      sender: "user",
      conv_id: convId,
      msg_id: msgId,
      session_id: id,
      collection_id: collections.activeCollectionId,
      video_id: videoId.value,
      content,
    };
    conversations[convId] = { [msgId]: message };
    useChatSocket().socket.emit("chat", message);
    addClientLoading(convId);
  }

  function addClientLoading(convId: string) {
    const loadingId = String(Date.now() + 2);
    conversations[convId][loadingId] = {
      conv_id: convId,
      msg_id: loadingId,
      session_id: sessionId.value!,
      msg_type: "output",
      sender: "assistant",
      clientLoading: true,
    };
  }

  function removeClientLoading(convId: string) {
    const conv = conversations[convId];
    const loading = Object.values(conv).find((m) => m.clientLoading);
    if (loading) delete conv[loading.msg_id];
  }

  let listening = false;
  function connect() {
    if (listening) return;
    listening = true;
    const { socket } = useChatSocket();

    socket.on("chat", (event: Message) => {
      if (event.session_id !== sessionId.value) return;
      const convId = String(event.conv_id);
      conversations[convId] ??= {};
      conversations[convId][String(event.msg_id)] = {
        ...event,
        sender: "assistant",
      };
      removeClientLoading(convId);
    });

    socket.on(
      "event",
      (event: {
        event_type: string;
        update: string;
        collection_id?: string;
      }) => {
        if (event.event_type !== "update_data") return;
        if (
          event.update === "videos" &&
          event.collection_id === collections.activeCollectionId
        ) {
          collections.refetch("video");
        }
        if (event.update === "collections") collections.load();
      },
    );
  }

  // Pasted or attached images upload as soon as they're queued.
  watch(chatAttachments, async (attachments) => {
    for (const attachment of attachments) {
      if (!attachment.upload || attachment.upload_status !== "in_queue")
        continue;
      attachment.upload_status = "uploading";
      try {
        const uploaded = await collectionsApi.uploadMedia({
          collectionId: collections.activeCollectionId!,
          sourceType: "file",
          source: attachment.image_data,
        });
        attachment.url = await collectionsApi.generateMediaUrl(
          "image",
          uploaded.collection_id,
          uploaded.id,
        );
        attachment.image_id = uploaded.id;
        attachment.upload_status = "complete";
      } catch {
        attachment.upload_status = "error";
      }
    }
  });

  return {
    sessionId,
    videoId,
    conversations,
    sessionLoading,
    chatInput,
    chatAttachments,
    chatLoading,
    isEmpty,
    reset,
    startNewSession,
    openSession,
    addMessage,
    connect,
  };
});
