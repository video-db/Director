<template>
  <Sidebar collapsible="offcanvas" label="Director">
    <SidebarHeader class="gap-12 px-12 pt-16">
      <RouterLink
        :to="{ name: 'home' }"
        class="flex h-32 items-center px-8"
        aria-label="Director home"
      >
        <Logo brand="director" :height="20" />
      </RouterLink>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            icon="edit_square"
            :active="route.name === 'home'"
            :disabled="!ready"
            @click="go({ name: 'home' })"
          >
            <span>New chat</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarHeader>

    <SidebarContent :class="{ 'pointer-events-none opacity-40': !ready }">
      <SidebarGroup>
        <SidebarGroupLabel>Collections</SidebarGroupLabel>
        <SidebarGroupAction
          icon="add"
          label="Create collection"
          @click="ui.showCreateCollection = true"
        />
        <!-- Capped so a long list doesn't push Chats out of view. -->
        <SidebarGroupContent class="max-h-224 overflow-y-auto">
          <SidebarMenu>
            <template v-if="!collections.loaded">
              <SidebarMenuItem v-for="n in 3" :key="n">
                <SidebarMenuSkeleton />
              </SidebarMenuItem>
            </template>
            <SidebarMenuItem v-for="c in collections.collections" :key="c.id">
              <SidebarMenuButton
                icon="folder"
                :active="route.name === 'collection' && route.params.collectionId === c.id"
                @click="go({ name: 'collection', params: { collectionId: c.id } })"
              >
                <span class="truncate">{{ c.name }}</span>
              </SidebarMenuButton>
              <SidebarMenuAction
                icon="delete"
                :label="`Delete ${c.name}`"
                show-on-hover
                @click="emit('delete-collection', c)"
              />
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <SidebarGroup>
        <SidebarGroupLabel>Chats</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem v-if="route.name === 'home'">
              <SidebarMenuButton active>
                <span class="text-text-neutral-tertiary">New chat</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem v-for="s in sessions.sessions" :key="s.session_id">
              <SidebarMenuButton
                :active="s.session_id === chat.sessionId"
                @click="go({ name: 'chat', params: { sessionId: s.session_id } })"
              >
                <span class="truncate">{{ sessionName(s) }}</span>
              </SidebarMenuButton>
              <SidebarMenuAction
                icon="delete"
                label="Delete chat"
                show-on-hover
                @click="ui.pendingDelete = { kind: 'session', id: s.session_id }"
              />
            </SidebarMenuItem>
            <li
              v-if="sessions.sessions.length === 0 && route.name !== 'home'"
              class="px-8 py-6 text-sm text-text-neutral-tertiary"
            >
              No chats yet
            </li>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>

    <SidebarFooter class="px-12 pb-16">
      <SidebarMenu>
        <SidebarMenuItem v-for="link in links" :key="link.href">
          <SidebarMenuButton as="a" :href="link.href" target="_blank" rel="noopener noreferrer" :icon="link.icon">
            <span>{{ link.text }}</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarFooter>
  </Sidebar>
</template>

<script setup lang="ts">
import { useRoute, useRouter, type RouteLocationRaw } from "vue-router";

import { Logo } from "@/components/ui/logo";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  useSidebar,
} from "@/components/ui/sidebar";
import { sidebarLinks as links } from "@/config";
import { useChatStore } from "@/stores/chat";
import { useCollectionsStore } from "@/stores/collections";
import { useSessionsStore } from "@/stores/sessions";
import { useUiStore } from "@/stores/ui";
import type { Collection, Session } from "@/types";

defineProps<{ ready: boolean }>();
const emit = defineEmits<{ "delete-collection": [Collection] }>();

const route = useRoute();
const router = useRouter();
const chat = useChatStore();
const collections = useCollectionsStore();
const sessions = useSessionsStore();
const ui = useUiStore();
const { isMobile, setOpenMobile } = useSidebar();

function go(to: RouteLocationRaw) {
  router.push(to);
  if (isMobile.value) setOpenMobile(false);
}

function sessionName(s: Session) {
  if (s.name) return s.name;
  return new Date(s.created_at * 1000).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>
