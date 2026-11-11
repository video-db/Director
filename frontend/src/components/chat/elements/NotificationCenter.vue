<template>
  <div
    class="vdb-c-pointer-events-none vdb-c-fixed vdb-c-left-1/2 vdb-c-top-20 vdb-c-z-50 vdb-c-flex -vdb-c-translate-x-1/2 vdb-c-flex-col vdb-c-gap-10"
  >
    <TransitionGroup
      name="notification"
      tag="div"
      class="vdb-c-flex vdb-c-flex-col vdb-c-gap-10"
    >
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="vdb-c-shadow-sm vdb-c-pointer-events-auto vdb-c-flex vdb-c-transform vdb-c-items-center vdb-c-rounded-lg vdb-c-px-20 vdb-c-py-10 vdb-c-text-base vdb-c-font-medium"
        :class="{
          '#EBF5ED vdb-c-border vdb-c-border-vdb-green vdb-c-bg-green-50 vdb-c-text-black':
            notification.type === 'success',
          'vdb-c-border vdb-c-border-red vdb-c-bg-red-200 vdb-c-text-black':
            notification.type === 'error',
        }"
        role="alert"
      >
        <div class="vdb-c-flex vdb-c-items-center vdb-c-gap-10">
          <div
            v-if="notification.icon"
            class="vdb-c-flex vdb-c-w-24 vdb-c-items-center vdb-c-justify-center"
          >
            <component :is="notification.icon" class="" />
          </div>
          <span class="vdb-c-text-sm md:vdb-c-text-base">{{
            notification.message
          }}</span>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { storeToRefs } from "pinia";
import { useUiStore } from "@/stores/ui";

const { toasts: notifications } = storeToRefs(useUiStore());
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateY(-30px) translateX(-50%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateY(-30px) translateX(-50%);
}

.notification-move {
  transition: transform 0.3s ease;
}
</style>
