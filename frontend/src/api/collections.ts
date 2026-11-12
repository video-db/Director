import type {
  Audio,
  Collection,
  Image,
  MediaKind,
  UploadRequest,
  Video,
} from "@/types";
import { json, request, requestText } from "./http";

const base = (collectionId: string) => `/videodb/collection/${collectionId}`;

interface MutationResult {
  success: boolean;
  message?: string;
}

type Uploaded = Pick<Video, "id" | "collection_id" | "name">;

export const listCollections = () =>
  request<Collection[]>("/videodb/collection");

export const getCollection = (id: string) => request<Collection>(base(id));

export const createCollection = (name: string, description: string) =>
  request<{ data: { collection: Collection } }>(
    "/videodb/collection",
    json("POST", { name, description }),
  ).then((res) => res.data.collection);

export const deleteCollection = (id: string) =>
  request<MutationResult>(base(id), json("DELETE"));

export const listVideos = (collectionId: string) =>
  request<Video[]>(`${base(collectionId)}/video`);

export const getVideo = (collectionId: string, videoId: string) =>
  request<Video>(`${base(collectionId)}/video/${videoId}`);

export const listAudios = (collectionId: string) =>
  request<Audio[]>(`${base(collectionId)}/audio`);

export const listImages = (collectionId: string) =>
  request<Image[]>(`${base(collectionId)}/image`);

export const deleteMedia = (
  kind: MediaKind,
  collectionId: string,
  mediaId: string,
) =>
  request<MutationResult>(
    `${base(collectionId)}/${kind}/${mediaId}`,
    json("DELETE"),
  );

export const generateMediaUrl = (
  kind: "audio" | "image",
  collectionId: string,
  mediaId: string,
) => requestText(`${base(collectionId)}/${kind}/${mediaId}/generate_url`);

export function uploadMedia({
  collectionId,
  sourceType,
  source,
}: UploadRequest) {
  const path = `${base(collectionId)}/upload`;
  if (sourceType === "file") {
    const form = new FormData();
    form.append("file", source as File);
    return request<Uploaded>(path, { method: "POST", body: form });
  }
  return request<Uploaded>(
    path,
    json("POST", {
      source: (source as { url: string }).url,
      source_type: "url",
    }),
  );
}
