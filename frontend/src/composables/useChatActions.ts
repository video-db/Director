import { useRoute, useRouter } from "vue-router";

import { useChatStore } from "@/stores/chat";
import type { ContentBase } from "@/types";

interface SendInput {
  text?: string;
  images?: { image_id?: string; url?: string }[];
}

// Sending from anywhere but an open chat starts a new session and opens it.
export function useChatActions() {
  const chat = useChatStore();
  const route = useRoute();
  const router = useRouter();

  function send({ text = "", images = [] }: SendInput) {
    const content: ContentBase[] = [];
    if (text) content.push({ type: "text", text });
    for (const image of images) {
      content.push({
        type: "image",
        image: { image_id: image.image_id, url: image.url },
      });
    }
    if (!content.length) return;

    if (route.name !== "chat" || !chat.sessionId) {
      const id = chat.startNewSession();
      router.push({ name: "chat", params: { sessionId: id } });
    }
    chat.addMessage(content);
  }

  return { send };
}
