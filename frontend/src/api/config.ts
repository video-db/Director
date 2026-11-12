import type { ConfigStatus } from "@/types";
import { request } from "./http";

export const checkConfig = () => request<ConfigStatus>("/config/check");
