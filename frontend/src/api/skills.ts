import type { CatalogSkill, SkillJob, SkillsOverview } from "@/types";
import { json, request } from "./http";

const enc = encodeURIComponent;

export const listSkills = () => request<SkillsOverview>("/skills");

export const getSourceStatus = () =>
  request<{ available: boolean; reason: string | null }>("/skills/source");

export const readSkill = (name: string) =>
  request<{ content: string }>(`/skills/installed/${enc(name)}`).then((r) => r.content);

export const searchSkills = (query: string) =>
  request<{ results: CatalogSkill[] }>(`/skills/search?q=${enc(query)}`).then((r) => r.results);

export const previewSkill = (source: string, skill: string) =>
  request<{ content: string }>(`/skills/preview?source=${enc(source)}&skill=${enc(skill)}`).then(
    (r) => r.content,
  );

export const installSkill = (source: string, skill: string) =>
  request<SkillJob>("/skills/install", json("POST", { source, skill }));

export const updateSkill = (name: string) =>
  request<SkillJob>(`/skills/installed/${enc(name)}/update`, json("POST"));

export const removeSkill = (name: string) =>
  request<{ message: string }>(`/skills/installed/${enc(name)}`, json("DELETE"));

export const getSkillJob = (id: string) => request<SkillJob>(`/skills/jobs/${enc(id)}`);

// Installs clone a git repo; poll until the job settles.
export async function waitForJob(job: SkillJob, intervalMs = 1000): Promise<SkillJob> {
  let current = job;
  while (current.status === "running") {
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    current = await getSkillJob(current.id);
  }
  return current;
}
