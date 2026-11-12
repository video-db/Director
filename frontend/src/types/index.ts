// Shapes returned by the Director backend (backend/director/core/session.py, tools/videodb_tool.py).

export type MsgStatus =
  | "progress"
  | "success"
  | "error"
  | "not_generated"
  | "overlimit"
  | "sessionlimit";

export type MsgType = "input" | "output" | "system";

export interface ConfigStatus {
  videodb_configured: boolean;
  llm_configured: boolean;
  db_configured: boolean;
}

export interface Collection {
  id: string;
  name: string;
  description?: string;
}

export interface Video {
  id: string;
  collection_id: string;
  name: string;
  description?: string;
  stream_url?: string;
  thumbnail_url?: string;
  external_url?: string;
  length?: number;
  type?: "video";
}

export interface Audio {
  id: string;
  collection_id: string;
  name: string;
  length?: number;
  url?: string;
  type?: "audio";
}

export interface Image {
  id: string;
  collection_id: string;
  name: string;
  url?: string;
  description?: string;
  type?: "image";
}

export type Media = Video | Audio | Image;
export type MediaKind = "video" | "audio" | "image";

export interface ContentBase {
  type: string;
  status?: MsgStatus;
  status_message?: string;
  agent_name?: string;
  [key: string]: unknown;
}

export interface Message {
  session_id: string;
  conv_id: string;
  msg_id: string;
  msg_type: MsgType;
  sender: "user" | "assistant";
  content?: ContentBase[];
  actions?: string[];
  // Tools that ran for this message, set by the backend.
  agents?: string[];
  status?: MsgStatus;
  collection_id?: string | null;
  video_id?: string | null;
  clientLoading?: boolean;
}

/** conv_id → msg_id → message */
export type Conversations = Record<string, Record<string, Message>>;

export interface Session {
  session_id: string;
  created_at: number;
  updated_at?: number;
  name?: string;
  video_id?: string | null;
  collection_id?: string | null;
}

export interface SessionDetail extends Session {
  conversation?: Message[];
}

export interface UploadRequest {
  collectionId: string;
  sourceType: "file" | "url";
  source: File | { url: string };
}

export interface ImageAttachment {
  type: "image";
  key: string;
  image_data: File;
  upload: boolean;
  upload_status: "in_queue" | "uploading" | "complete" | "error";
  image_id?: string;
  url?: string;
}
