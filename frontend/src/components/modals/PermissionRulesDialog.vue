<template>
  <Dialog v-model:open="open">
    <DialogContent>
      <DialogHeader title="Always-allowed actions" />
      <DialogBody>
        <p class="text-sm text-text-neutral-secondary">
          Director runs these in every chat without asking. Remove one to be asked again.
        </p>
        <div v-if="loading" class="flex justify-center py-24">
          <Spinner label="Loading rules" />
        </div>
        <p v-else-if="error" class="text-sm text-text-error-primary">{{ error }}</p>
        <EmptyState
          v-else-if="rules.length === 0"
          icon="shield"
          title="No rules yet"
          description="Choose “Always allow” on an approval card to add one."
        />
        <ItemGroup v-else class="gap-8">
          <Item v-for="rule in rules" :key="rule.rule_id" variant="outline" size="sm">
            <ItemContent class="min-w-0">
              <ItemTitle>{{ toolName(rule.agent) }}</ItemTitle>
              <ItemDescription>
                <code class="break-all font-mono text-xs">{{ describe(rule.pattern) }}</code>
              </ItemDescription>
            </ItemContent>
            <ItemActions>
              <IconButton
                icon="delete"
                :label="`Remove the rule for ${describe(rule.pattern)}`"
                hierarchy="tertiary"
                size="sm"
                :disabled="removing === rule.rule_id"
                @click="remove(rule)"
              />
            </ItemActions>
          </Item>
        </ItemGroup>
      </DialogBody>
      <DialogFooter>
        <Button hierarchy="primary" @click="open = false">Done</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

import { deletePermissionRule, listPermissionRules } from "@/api/config";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { IconButton } from "@/components/ui/icon-button";
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemTitle,
} from "@/components/ui/item";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/components/ui/toast";
import type { PermissionRule } from "@/types";

const open = defineModel<boolean>("open", { default: false });
const { toast } = useToast();

const rules = ref<PermissionRule[]>([]);
const loading = ref(false);
const error = ref("");
const removing = ref<string | null>(null);

const TOOL_NAMES: Record<string, string> = {
  bash_executor: "Command",
  code_executor: "Python",
};

watch(open, async (isOpen) => {
  if (!isOpen) return;
  loading.value = true;
  error.value = "";
  try {
    rules.value = await listPermissionRules();
  } catch {
    error.value = "Couldn't load the rules.";
  } finally {
    loading.value = false;
  }
});

function toolName(agent: string) {
  return TOOL_NAMES[agent] ?? agent;
}

// Keys look like "bash_executor:ffprobe -v | ls"; the part after the colon is what matches.
function describe(pattern: string) {
  const rest = pattern.slice(pattern.indexOf(":") + 1);
  return pattern.startsWith("code_executor:") ? rest.split(",").join(", ") : rest;
}

async function remove(rule: PermissionRule) {
  removing.value = rule.rule_id;
  try {
    await deletePermissionRule(rule.rule_id);
    rules.value = rules.value.filter((r) => r.rule_id !== rule.rule_id);
  } catch {
    toast.error("Couldn't remove the rule");
  } finally {
    removing.value = null;
  }
}
</script>
