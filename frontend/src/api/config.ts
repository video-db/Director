import type { ConfigStatus, PermissionRule, PermissionsConfig } from "@/types";
import { json, request } from "./http";

export const checkConfig = () => request<ConfigStatus>("/config/check");

export const getPermissions = () => request<PermissionsConfig>("/config/permissions");

export const listPermissionRules = () =>
  request<{ rules: PermissionRule[] }>("/config/permission-rules").then((r) => r.rules);

export const deletePermissionRule = (ruleId: string) =>
  request<{ message: string }>(
    `/config/permission-rules/${encodeURIComponent(ruleId)}`,
    json("DELETE"),
  );
