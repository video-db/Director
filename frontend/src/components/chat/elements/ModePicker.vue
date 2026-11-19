<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <MenuButton :icon="current.icon" size="sm" aria-label="Permission mode" :title="current.hint">
        {{ current.label }}
      </MenuButton>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" class="w-288">
      <DropdownMenuLabel>Permission mode</DropdownMenuLabel>
      <p v-if="config.permissions && !config.permissions.isolated" class="px-8 pb-6 text-xs text-text-neutral-tertiary">
        Code runs on this machine without a sandbox, so Director asks first by default.
      </p>
      <DropdownMenuRadioGroup :model-value="chat.mode" @update:model-value="(v) => chat.setMode(v as PermissionMode)">
        <DropdownMenuRadioItem
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :text-value="option.label"
          :icon="option.icon"
          class="h-auto items-start py-6"
        >
          <span class="flex flex-col whitespace-normal">
            <span>{{ option.label }}</span>
            <span class="text-xs text-text-neutral-tertiary">{{ option.hint }}</span>
          </span>
        </DropdownMenuRadioItem>
      </DropdownMenuRadioGroup>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import { computed } from "vue";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
  MenuButton,
} from "@/components/ui/dropdown-menu";
import { useChatStore } from "@/stores/chat";
import { useConfigStore } from "@/stores/config";
import type { PermissionMode } from "@/types";

const MODE_OPTIONS: { value: PermissionMode; label: string; icon: string; hint: string }[] = [
  { value: "read_only", label: "Read-only", icon: "visibility", hint: "Looks at your media and reads files. Asks before changing anything." },
  { value: "ask", label: "Ask", icon: "front_hand", hint: "Asks before every code or command run." },
  { value: "auto", label: "Auto", icon: "bolt", hint: "Runs on its own after a safety check. Asks before deleting or anything risky." },
  { value: "full", label: "Full access", icon: "lock_open", hint: "Never asks. Blocked commands stay blocked." },
];

const chat = useChatStore();
const config = useConfigStore();
// Only the modes this server allows, e.g. no Full access without a sandbox.
const options = computed(() =>
  MODE_OPTIONS.filter((o) => !chat.allowedModes || chat.allowedModes.includes(o.value)),
);
const current = computed(() => MODE_OPTIONS.find((o) => o.value === chat.mode) ?? MODE_OPTIONS[1]);
</script>
