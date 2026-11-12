// Backend setup status and the agent list.
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as api from "@/api/agents";
import type { Agent, ConfigStatus } from "@/types";

export const useAgentsStore = defineStore("agents", () => {
  const configStatus = ref<ConfigStatus | null>(null);
  const backendUnreachable = ref(false);
  const agents = ref<Agent[]>([]);

  const isSetupComplete = computed(
    () =>
      !!configStatus.value &&
      Object.values(configStatus.value).every((value) => value === true),
  );

  let pending: Promise<void> | null = null;

  function loadConfig(force = false) {
    if (force) pending = null;
    pending ??= api
      .checkConfig()
      .then((status) => {
        configStatus.value = status;
        backendUnreachable.value = false;
      })
      .catch(() => {
        backendUnreachable.value = true;
        pending = null;
      });
    return pending;
  }

  async function loadAgents() {
    agents.value = await api.listAgents();
  }

  return {
    configStatus,
    backendUnreachable,
    agents,
    isSetupComplete,
    loadConfig,
    loadAgents,
  };
});
