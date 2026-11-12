import { io, type Socket } from "socket.io-client";
import { ref } from "vue";

import { socketUrl } from "@/config";

// One socket per tab, shared by every store that talks to /chat.
let socket: Socket | null = null;
const isConnected = ref(false);

export function useChatSocket() {
  if (!socket) {
    socket = io(socketUrl);
    socket.on("connect", () => (isConnected.value = true));
    socket.on("disconnect", () => (isConnected.value = false));
  }
  return { socket, isConnected };
}
