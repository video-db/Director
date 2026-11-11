import type { Session, SessionDetail } from "@/types";
import { json, request } from "./http";

export const listSessions = () => request<Session[]>("/session");

export const getSession = (id: string) =>
  request<SessionDetail>(`/session/${id}`);

export const deleteSession = (id: string) =>
  request<{ message: string }>(`/session/${id}`, json("DELETE"));
