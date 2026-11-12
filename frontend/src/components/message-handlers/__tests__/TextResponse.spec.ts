import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/composables/useChatSocket", () => ({
  useChatSocket: () => ({ socket: { emit: vi.fn(), on: vi.fn() } }),
}));

import { useChatStore } from "@/stores/chat";
import TextResponse from "../TextResponse.vue";

const REPLY_LABEL = "Here is your response";

function renderAll(status: string) {
  const chat = useChatStore();
  chat.conversations.c1 = {
    m1: {
      msg_id: "m1",
      conv_id: "c1",
      msg_type: "output",
      sender: "assistant",
      status,
      content: [
        { type: "text", agent_name: "assistant", status: "success", text: "Let me check that." },
        { type: "text", agent_name: "code_executor", status: "success", text: "```python\nprint(1)\n```" },
        { type: "text", agent_name: "assistant", status: "success", text: "All done." },
      ],
    },
  } as any;
  return chat.conversations.c1.m1.content!.map((content) =>
    mount(TextResponse, { props: { content, convId: "c1", msgId: "m1" } }).text(),
  );
}

describe("TextResponse", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("labels only the last assistant text as the reply", () => {
    const [interim, tool, final] = renderAll("success");
    expect(interim).toContain("Let me check that.");
    expect(interim).not.toContain(REPLY_LABEL);
    expect(tool).toContain(REPLY_LABEL); // tool blocks keep their own header
    expect(final).toContain(REPLY_LABEL);
  });

  it("labels no assistant text as the reply while the turn is running", () => {
    const [interim, , last] = renderAll("progress");
    expect(interim).not.toContain(REPLY_LABEL);
    expect(last).not.toContain(REPLY_LABEL);
  });
});
