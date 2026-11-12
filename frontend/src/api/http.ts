import { backendUrl } from "@/config";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function send(path: string, init: RequestInit): Promise<Response> {
  const res = await fetch(`${backendUrl}${path}`, init);
  if (!res.ok) {
    // The backend reports failures as { message }.
    const body = await res.json().catch(() => null);
    throw new ApiError(body?.message || res.statusText, res.status);
  }
  return res;
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await send(path, init);
  return res.json() as Promise<T>;
}

export async function requestText(path: string): Promise<string> {
  const res = await send(path, {});
  return res.text();
}

export const json = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: body === undefined ? undefined : JSON.stringify(body),
});
