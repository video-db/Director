<template>
  <div
    class="vdb-c-flex vdb-c-w-full vdb-c-flex-1 vdb-c-flex-col vdb-c-items-center vdb-c-justify-center vdb-c-gap-24"
  >
    <SetupScreen
      v-if="config.configStatus && !config.backendUnreachable"
      :config-status="config.configStatus"
    />
    <div
      v-else
      class="vdb-c-flex vdb-c-max-w-[480px] vdb-c-flex-col vdb-c-gap-8 vdb-c-text-center"
    >
      <p class="vdb-c-text-xl vdb-c-font-semibold vdb-c-text-kilvish-900">
        Can't reach the Director backend
      </p>
      <p class="vdb-c-text-sm vdb-c-text-vdb-darkishgrey">
        Make sure it's running at
        <code class="vdb-c-rounded-4 vdb-c-bg-kilvish-200 vdb-c-px-4">{{
          backendUrl
        }}</code>
        or set <code>VITE_APP_BACKEND_URL</code> in <code>.env</code>.
      </p>
    </div>
    <Button variant="secondary" :disabled="checking" @click="recheck">
      {{ checking ? "Checking…" : "Check again" }}
    </Button>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "@/components/buttons/Button.vue";
import SetupScreen from "@/components/chat/elements/SetupScreen.vue";
import { backendUrl } from "@/config";
import { useConfigStore } from "@/stores/config";

const route = useRoute();
const router = useRouter();
const config = useConfigStore();
const checking = ref(false);

async function recheck() {
  checking.value = true;
  await config.loadConfig(true);
  checking.value = false;
  if (config.isSetupComplete) {
    router.replace((route.query.redirect as string) || { name: "home" });
  }
}
</script>
