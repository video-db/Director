import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

const handlers: Record<string, (event: any) => void> = {};
const emit = vi.fn();
vi.mock("@/composables/useChatSocket", () => ({
  useChatSocket: () => ({
    socket: { emit, on: (name: string, fn: any) => (handlers[name] = fn) },
  }),
}));

const getSession = vi.fn();
vi.mock("@/api/sessions", () => ({
  getSession: (id: string) => getSession(id),
}));
vi.mock("@/api/collections", () => ({
  listVideos: vi.fn(async () => []),
  listAudios: vi.fn(async () => []),
  listImages: vi.fn(async () => []),
}));

import { useChatStore } from "../chat";

describe("chat store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    emit.mockClear();
    getSession.mockReset();
  });

  it("loads a session's messages grouped by conversation", async () => {
    getSession.mockResolvedValue({
      session_id: "s1",
      created_at: 1,
      conversation: [
        { conv_id: 1, msg_id: 2, msg_type: "input", content: [] },
        { conv_id: 1, msg_id: 3, msg_type: "output", content: [] },
      ],
    });
    const chat = useChatStore();
    await chat.openSession("s1");
    expect(Object.keys(chat.conversations)).toEqual(["1"]);
    expect(chat.conversations["1"]["2"].sender).toBe("user");
    expect(chat.conversations["1"]["3"].sender).toBe("assistant");
    expect(chat.sessionLoading).toBe(false);
  });

  it("shows an unknown session as empty", async () => {
    getSession.mockRejectedValue(new Error("Session not found."));
    const chat = useChatStore();
    await chat.openSession("missing");
    expect(chat.isEmpty).toBe(true);
    expect(chat.sessionId).toBe("missing");
  });

  it("sends a message and shows a loader until the reply", () => {
    const chat = useChatStore();
    chat.connect();
    const id = chat.startNewSession();
    chat.addMessage([{ type: "text", text: "hi" }]);

    const sent = emit.mock.calls[0];
    expect(sent[0]).toBe("chat");
    expect(sent[1]).toMatchObject({ session_id: id });
    expect(sent[1]).not.toHaveProperty("agents");
    expect(chat.chatLoading).toBe(true);

    const convId = sent[1].conv_id;
    handlers.chat({
      session_id: id,
      conv_id: convId,
      msg_id: "99",
      msg_type: "output",
      status: "success",
      content: [],
    });
    expect(chat.chatLoading).toBe(false);
    expect(chat.conversations[convId]["99"].sender).toBe("assistant");
  });

  it("ignores replies for other sessions", () => {
    const chat = useChatStore();
    chat.connect();
    chat.startNewSession();
    handlers.chat({ session_id: "other", conv_id: "1", msg_id: "2" });
    expect(chat.isEmpty).toBe(true);
  });
});
