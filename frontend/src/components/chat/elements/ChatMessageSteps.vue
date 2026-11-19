<template>
  <Collapsible v-model:open="open" class="flex flex-col gap-8">
    <CollapsibleTrigger
      class="group flex w-fit items-center gap-4 rounded-xxs text-sm font-medium text-text-neutral-secondary outline-none hover:text-text-neutral-primary focus-visible:shadow-focus-ring"
    >
      <Spinner v-if="status === 'progress'" size="sm" decorative class="mr-4" />
      Director's log
      <span class="font-normal text-text-neutral-tertiary">· {{ steps.length || 1 }} {{ steps.length === 1 ? "step" : "steps" }}</span>
      <Icon
        name="keyboard_arrow_down"
        :size="16"
        class="transition-transform group-data-[state=open]:rotate-180"
      />
    </CollapsibleTrigger>
    <CollapsibleContent>
      <div class="flex flex-col gap-4 border-l border-border-neutral-primary pl-12">
        <LogStep
          v-for="(step, i) in displaySteps"
          :key="i"
          :label="step"
          :status="stepStatus(i)"
        />
      </div>
    </CollapsibleContent>
  </Collapsible>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Icon } from "@/components/ui/icon";
import { LogStep } from "@/components/ui/log-step";
import { Spinner } from "@/components/ui/spinner";

const props = withDefaults(
  defineProps<{ steps?: string[]; status?: string; expanded?: boolean }>(),
  { steps: () => [], status: "progress", expanded: false },
);

const open = ref(props.expanded);
// Collapses once the turn finishes; the user can reopen it.
watch(
  () => props.expanded,
  (v) => {
    if (!v) open.value = false;
  },
);

const displaySteps = computed(() => (props.steps.length ? props.steps : ["Thinking"]));

function stepStatus(i: number): "running" | "done" | "failed" {
  if (i < displaySteps.value.length - 1) return "done";
  if (props.status === "progress") return "running";
  return props.status === "error" ? "failed" : "done";
}
</script>
