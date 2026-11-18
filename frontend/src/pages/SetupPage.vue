<template>
  <div class="mx-auto flex min-h-full w-full max-w-640 flex-col justify-center gap-24 px-16 py-40 md:px-24">
    <template v-if="config.configStatus && !config.backendUnreachable">
      <SetupScreen :config-status="config.configStatus" />
      <Button class="self-start" hierarchy="secondary" icon="refresh" :loading="checking" @click="recheck">
        Check again
      </Button>
    </template>

    <EmptyState
      v-else
      icon="cloud_off"
      :level="2"
      title="Can't reach the Director backend"
      :description="`Make sure it's running at ${backendUrl}, or point the app at it with VITE_APP_BACKEND_URL in frontend/.env.`"
    >
      <CodeBlock class="text-left" :code="`VITE_APP_BACKEND_URL=${backendUrl}`" title="frontend/.env" />
      <Button hierarchy="secondary" icon="refresh" :loading="checking" @click="recheck">
        Check again
      </Button>
    </EmptyState>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import SetupScreen from "@/components/chat/elements/SetupScreen.vue";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import { EmptyState } from "@/components/ui/empty-state";
import { backendUrl } from "@/config";
import { useConfigStore } from "@/stores/config";

const route = useRoute();
const router = useRouter();
const config = useConfigStore();
const checking = ref(false);

async function recheck() {
  checking.value = true;
  try {
    await config.loadConfig(true);
  } finally {
    checking.value = false;
  }
  if (config.isSetupComplete) {
    router.replace((route.query.redirect as string) || { name: "home" });
  }
}
</script>
