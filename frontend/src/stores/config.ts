// Backend setup status.
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as api from "@/api/config";
import type { ConfigStatus } from "@/types";

export const useConfigStore = defineStore("config", () => {
  const configStatus = ref<ConfigStatus | null>(null);
  const backendUnreachable = ref(false);

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

  return {
    configStatus,
    backendUnreachable,
    isSetupComplete,
    loadConfig,
  };
});
