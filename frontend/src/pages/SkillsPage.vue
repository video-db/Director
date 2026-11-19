<template>
  <div class="mx-auto flex w-full max-w-960 flex-col gap-24 px-16 py-24 md:px-24">
    <SectionHeader
      title="Skills"
      description="Skills teach Director how to do things. Director reads them from your skills folder, so they apply to every chat as soon as they're added."
    />

    <Alert v-if="overview && !overview.manage.enabled" status="warning">
      {{ overview.manage.reason }}
    </Alert>

    <Alert v-for="m in overview?.missing_required ?? []" :key="m.skill" status="warning" icon="extension">
      <span class="flex flex-wrap items-center justify-between gap-8">
        <span>Director needs the <code class="font-mono">{{ m.skill }}</code> skill for VideoDB work, and it isn't installed.</span>
        <Button
          v-if="overview?.manage.enabled"
          size="sm"
          hierarchy="primary"
          :loading="busy[m.skill] === 'install'"
          @click="install(m.source, m.skill)"
        >
          Install {{ m.skill }}
        </Button>
      </span>
    </Alert>

    <Tabs v-model="tab">
      <TabsList variant="line">
        <TabsTrigger value="installed" icon="extension">Installed</TabsTrigger>
        <TabsTrigger value="browse" icon="search" :disabled="overview ? !overview.manage.enabled : true">
          Browse
        </TabsTrigger>
      </TabsList>

      <TabsContent value="installed" class="pt-16">
        <div v-if="!overview && !loadError" class="flex justify-center py-48">
          <Spinner label="Loading skills" />
        </div>
        <Alert v-else-if="loadError" status="error">{{ loadError }}</Alert>
        <EmptyState
          v-else-if="overview && overview.skills.length === 0"
          icon="extension"
          title="No skills yet"
          description="Browse to find skills to add."
        />
        <ItemGroup v-else-if="overview" class="gap-8">
          <Item v-for="skill in overview.skills" :key="skill.name" variant="outline" size="sm">
            <ItemContent class="min-w-0">
              <ItemTitle class="flex flex-wrap items-center gap-6">
                {{ skill.name }}
                <Badge v-if="skill.problem" colour="error" size="sm">Can't be used</Badge>
                <Badge v-if="skill.linked" colour="neutral" size="sm">Linked</Badge>
              </ItemTitle>
              <ItemDescription class="line-clamp-2">
                {{ skill.problem ?? skill.description }}
              </ItemDescription>
              <p class="text-xs text-text-neutral-tertiary">
                {{ skill.source ? `From ${skill.source}` : "Added outside Director" }}
              </p>
            </ItemContent>
            <ItemActions class="shrink-0">
              <Button size="sm" hierarchy="tertiary" @click="previewInstalled(skill.name)">Preview</Button>
              <Button
                v-if="skill.source && overview.manage.enabled"
                size="sm"
                hierarchy="tertiary"
                :loading="busy[skill.name] === 'update'"
                :disabled="!!busy[skill.name]"
                @click="update(skill.name)"
              >
                Update
              </Button>
              <IconButton
                v-if="overview.manage.enabled"
                icon="delete"
                :label="`Remove ${skill.name}`"
                hierarchy="tertiary"
                size="sm"
                :disabled="!!busy[skill.name]"
                @click="pendingRemove = skill"
              />
            </ItemActions>
          </Item>
        </ItemGroup>
      </TabsContent>

      <TabsContent value="browse" class="flex flex-col gap-16 pt-16">
        <div v-if="sourceState === 'checking'" class="flex items-center gap-8 text-sm text-text-neutral-secondary">
          <Spinner size="sm" decorative /> Checking the skills CLI…
        </div>
        <Alert v-else-if="sourceProblem" status="warning">{{ sourceProblem }}</Alert>
        <template v-else>
          <form class="flex gap-8" @submit.prevent="search">
            <Input
              v-model="query"
              leading-icon="search"
              placeholder="Search skills, e.g. video, pdf, slides"
              aria-label="Search skills"
              class="min-w-0 flex-1"
            />
            <Button type="submit" hierarchy="secondary" :loading="searching" :disabled="!query.trim()">Search</Button>
          </form>
          <Alert v-if="searchError" status="error">{{ searchError }}</Alert>
          <p v-else-if="searched && results.length === 0" class="text-sm text-text-neutral-secondary">
            No skills match “{{ searched }}”.
          </p>
          <ItemGroup v-else class="gap-8">
            <Item v-for="r in results" :key="`${r.source}@${r.skill}`" variant="outline" size="sm">
              <ItemContent class="min-w-0">
                <ItemTitle>{{ r.skill }}</ItemTitle>
                <ItemDescription>
                  {{ r.source }}<template v-if="r.installs"> · {{ r.installs }} installs</template>
                </ItemDescription>
              </ItemContent>
              <ItemActions class="shrink-0">
                <Button size="sm" hierarchy="tertiary" @click="previewCatalog(r)">Preview</Button>
                <Badge v-if="installedNames.has(r.skill)" colour="success" size="sm">Installed</Badge>
                <Button
                  v-else
                  size="sm"
                  hierarchy="secondary"
                  :loading="busy[r.skill] === 'install'"
                  :disabled="!!busy[r.skill]"
                  @click="install(r.source, r.skill)"
                >
                  Install
                </Button>
              </ItemActions>
            </Item>
          </ItemGroup>
        </template>
      </TabsContent>
    </Tabs>

    <SkillPreviewDrawer
      v-model:open="preview.open"
      :title="preview.title"
      :subtitle="preview.subtitle"
      :content="preview.content"
      :loading="preview.loading"
      :error="preview.error"
    >
      <template v-if="preview.catalog" #footer>
        <p class="text-xs text-text-neutral-tertiary">
          Skills can run code on this machine. Install only from sources you trust.
        </p>
        <Button
          v-if="!installedNames.has(preview.catalog.skill)"
          hierarchy="primary"
          :loading="busy[preview.catalog.skill] === 'install'"
          @click="install(preview.catalog.source, preview.catalog.skill)"
        >
          Install {{ preview.catalog.skill }}
        </Button>
      </template>
    </SkillPreviewDrawer>

    <ConfirmationDialog
      :open="!!pendingRemove"
      :title="`Remove ${pendingRemove?.name ?? 'this skill'}?`"
      :description="
        pendingRemove?.linked
          ? 'Only the link in your skills folder is removed; the folder it points to stays.'
          : 'Its folder is deleted from your skills folder. Director stops using it from the next message.'
      "
      confirm-label="Remove"
      confirm-icon="delete"
      @update:open="(v) => !v && (pendingRemove = null)"
      @confirm="remove"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import * as api from "@/api/skills";
import SkillPreviewDrawer from "@/components/skills/SkillPreviewDrawer.vue";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { IconButton } from "@/components/ui/icon-button";
import { Input } from "@/components/ui/input";
import { Item, ItemActions, ItemContent, ItemDescription, ItemGroup, ItemTitle } from "@/components/ui/item";
import { SectionHeader } from "@/components/ui/section-header";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { useChatStore } from "@/stores/chat";
import type { CatalogSkill, InstalledSkill, SkillJob, SkillsOverview } from "@/types";

const { toast } = useToast();
useChatStore().reset();

const overview = ref<SkillsOverview | null>(null);
const loadError = ref("");
const tab = ref<"installed" | "browse">("installed");
// What's running per skill name, so its buttons show progress.
const busy = reactive<Record<string, "install" | "update" | undefined>>({});
const pendingRemove = ref<InstalledSkill | null>(null);

const installedNames = computed(
  () => new Set((overview.value?.skills ?? []).filter((s) => !s.problem).map((s) => s.name)),
);

async function load() {
  try {
    overview.value = await api.listSkills();
    loadError.value = "";
  } catch (e) {
    loadError.value = `Couldn't load skills: ${(e as Error).message}`;
  }
}
load();

// ---- browse ----
const sourceState = ref<"unknown" | "checking" | "ready">("unknown");
const sourceProblem = ref("");
const query = ref("");
const searched = ref("");
const searching = ref(false);
const searchError = ref("");
const results = ref<CatalogSkill[]>([]);

// The first check can take a while: npx may download the CLI.
watch(tab, async (value) => {
  if (value !== "browse" || sourceState.value !== "unknown") return;
  sourceState.value = "checking";
  try {
    const status = await api.getSourceStatus();
    sourceProblem.value = status.available ? "" : (status.reason ?? "The skills CLI isn't available.");
  } catch (e) {
    sourceProblem.value = (e as Error).message;
  }
  sourceState.value = "ready";
});

async function search() {
  const q = query.value.trim();
  if (!q) return;
  searching.value = true;
  searchError.value = "";
  try {
    results.value = await api.searchSkills(q);
    searched.value = q;
  } catch (e) {
    searchError.value = (e as Error).message;
  } finally {
    searching.value = false;
  }
}

// ---- preview ----
const preview = reactive({
  open: false,
  title: "",
  subtitle: "",
  content: "",
  loading: false,
  error: "",
  catalog: null as CatalogSkill | null,
});

async function showPreview(title: string, subtitle: string, load: () => Promise<string>, catalog: CatalogSkill | null) {
  Object.assign(preview, { open: true, title, subtitle, content: "", loading: true, error: "", catalog });
  try {
    preview.content = await load();
  } catch (e) {
    preview.error = (e as Error).message;
  } finally {
    preview.loading = false;
  }
}

function previewInstalled(name: string) {
  const skill = overview.value?.skills.find((s) => s.name === name);
  showPreview(name, skill?.source ? `From ${skill.source}` : "Added outside Director", () => api.readSkill(name), null);
}

function previewCatalog(r: CatalogSkill) {
  showPreview(r.skill, r.source, () => api.previewSkill(r.source, r.skill), r);
}

// ---- changes ----
async function runJob(name: string, kind: "install" | "update", start: () => Promise<SkillJob>) {
  busy[name] = kind;
  try {
    const job = await api.waitForJob(await start());
    if (job.status === "failed") throw new Error(job.error ?? "Something went wrong");
    toast.success(`${kind === "install" ? "Installed" : "Updated"} ${name}${securityNote(job.result?.security)}`);
    await load();
  } catch (e) {
    toast.error(`Couldn't ${kind} ${name}: ${(e as Error).message}`);
  } finally {
    busy[name] = undefined;
  }
}

const install = (source: string, skill: string) =>
  runJob(skill, "install", () => api.installSkill(source, skill));
const update = (name: string) => runJob(name, "update", () => api.updateSkill(name));

async function remove() {
  const skill = pendingRemove.value;
  pendingRemove.value = null;
  if (!skill) return;
  try {
    await api.removeSkill(skill.name);
    toast.success(`Removed ${skill.name}`);
    await load();
  } catch (e) {
    toast.error(`Couldn't remove ${skill.name}: ${(e as Error).message}`);
  }
}

// skills.sh scans each repo; surface anything other than a clean result.
function securityNote(security?: Record<string, string>) {
  const flagged = Object.entries(security ?? {}).filter(
    ([key, value]) => key !== "details" && !/^(safe|0 alerts|pass|none)$/i.test(value),
  );
  return flagged.length ? ` (scan: ${flagged.map(([k, v]) => `${k} ${v}`).join(", ")})` : "";
}
</script>
