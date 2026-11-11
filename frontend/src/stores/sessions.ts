// The sidebar's session list.
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as api from "@/api/sessions";
import type { Session } from "@/types";

export const useSessionsStore = defineStore("sessions", () => {
  const sessions = ref<Session[]>([]);

  const sorted = computed(() =>
    [...sessions.value].sort((a, b) => b.created_at - a.created_at),
  );

  async function load() {
    sessions.value = await api.listSessions();
  }

  // A session only exists on the backend after its first message.
  function track(sessionId: string) {
    if (sessions.value.some((s) => s.session_id === sessionId)) return;
    sessions.value.push({
      session_id: sessionId,
      created_at: Date.now() / 1000,
    });
  }

  async function remove(sessionId: string) {
    await api.deleteSession(sessionId);
    sessions.value = sessions.value.filter((s) => s.session_id !== sessionId);
  }

  return { sessions: sorted, load, track, remove };
});
