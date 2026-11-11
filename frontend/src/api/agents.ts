import type { Agent, ConfigStatus } from "@/types";
import { request } from "./http";

export const listAgents = () => request<Agent[]>("/agent");

export const checkConfig = () => request<ConfigStatus>("/config/check");
