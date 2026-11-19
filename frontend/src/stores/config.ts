// Backend setup status.
import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as api from "@/api/config";
import type { ConfigStatus, PermissionsConfig } from "@/types";

export const useConfigStore = defineStore("config", () => {
  const configStatus = ref<ConfigStatus | null>(null);
  const backendUnreachable = ref(false);
  // Null until loaded; the mode picker then offers only what the server allows.
  const permissions = ref<PermissionsConfig | null>(null);

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

  async function loadPermissions() {
    try {
      permissions.value = await api.getPermissions();
    } catch {
      // Keep the picker as it is; the server still caps the mode it receives.
    }
  }

  return {
    configStatus,
    permissions,
    loadPermissions,
    backendUnreachable,
    isSetupComplete,
    loadConfig,
  };
});
