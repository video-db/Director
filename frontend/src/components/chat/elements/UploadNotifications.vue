<!-- UploadNotifications.vue -->
<template>
  <div
    class="vdb-c-absolute vdb-c-bottom-4 vdb-c-right-24 vdb-c-z-50 vdb-c-flex vdb-c-flex-col vdb-c-gap-2"
  >
    <TransitionGroup name="notification">
      <div
        v-for="upload in uploads"
        :key="upload.id"
        class="vdb-c-flex vdb-c-h-[80px] vdb-c-w-[400px] vdb-c-cursor-pointer vdb-c-items-center vdb-c-rounded-lg vdb-c-border-2 vdb-c-border-roy vdb-c-bg-white hover:vdb-c-bg-gray-100"
      >
        <div
          class="flex items-center justify-center vdb-c-rounded-full vdb-c-px-20 vdb-c-py-14"
        >
          <div
            class="vdb-c-flex vdb-c-h-54 vdb-c-w-54 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full"
            :class="{
              'vdb-c-bg-orange-100': upload.status === 'loading',
              'vdb-c-bg-green-100': upload.status === 'success',
              'vdb-c-bg-red-100': upload.status === 'error',
            }"
          >
            <div v-if="upload.status === 'loading'" class="vdb-c-p-12">
              <FileUpload class="vdb-c-text-orange" fill="#EC5B16" />
            </div>
            <svg
              v-else-if="upload.status === 'success'"
              xmlns="http://www.w3.org/2000/svg"
              width="30"
              height="30"
              viewBox="0 0 30 30"
              class="vdb-c-text-success-700"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M25.0605 7.93945C25.6462 8.52513 25.6462 9.47487 25.0605 10.0605L13.0605 22.0605C12.4748 22.6462 11.5252 22.6462 10.9395 22.0605L4.93945 16.0605C4.35376 15.4748 4.35376 14.5252 4.93945 13.9395C5.52513 13.3538 6.47487 13.3538 7.06055 13.9395L12 18.8789L22.9395 7.93945C23.5252 7.35376 24.4748 7.35376 25.0605 7.93945Z"
                clip-rule="evenodd"
              />
            </svg>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              width="30"
              height="30"
              viewBox="0 0 30 30"
              class="vdb-c-text-danger-700"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M6.43945 6.43945C7.02513 5.85376 7.97487 5.85376 8.56055 6.43945L15 12.8789L21.4395 6.43945C22.0252 5.85376 22.9748 5.85376 23.5605 6.43945C24.1462 7.02513 24.1462 7.97487 23.5605 8.56055L17.1211 15L23.5605 21.4395C24.1462 22.0252 24.1462 22.9748 23.5605 23.5605C22.9748 24.1462 22.0252 24.1462 21.4395 23.5605L15 17.1211L8.56055 23.5605C7.97487 24.1462 7.02513 24.1462 6.43945 23.5605C5.85376 22.9748 5.85376 22.0252 6.43945 21.4395L12.8789 15L6.43945 8.56055C5.85376 7.97487 5.85376 7.02513 6.43945 6.43945Z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
        </div>
        <div
          class="vdb-c-flex vdb-c-flex-col vdb-c-gap-4 vdb-c-border-l vdb-c-border-roy vdb-c-p-16"
        >
          <h4 class="vdb-c-font-semibold vdb-c-text-kilvish-900">
            <span
              class="vdb-c-block vdb-c-max-w-[200px] vdb-c-truncate vdb-c-text-base vdb-c-font-semibold vdb-c-text-kilvish-900 sm:vdb-c-text-lg"
              :title="upload.name"
            >
              {{ upload.name }}
            </span>
          </h4>
          <p class="vdb-c-text-sm vdb-c-text-vdb-darkishgrey">
            <span
              class="vdb-c-line-clamp-2 vdb-c-text-xs vdb-c-font-normal sm:vdb-c-text-sm"
              :class="{
                'vdb-c-text-orange': upload.status === 'loading',
                'vdb-c-text-success-700': upload.status === 'success',
                'vdb-c-text-danger-700': upload.status === 'error',
              }"
            >
              <template v-if="upload.description">
                {{ upload.description }}
              </template>
              <template v-else>
                <template v-if="upload.status === 'loading'">
                  Uploading<span class="loading-dots"></span>
                </template>
                <template v-else-if="upload.status === 'success'">
                  Upload complete
                </template>
                <template v-else> Upload failed </template>
              </template>
            </span>
          </p>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { storeToRefs } from "pinia";
import { useUiStore } from "@/stores/ui";
import FileUpload from "../../icons/FileUpload.vue";

const { uploads } = storeToRefs(useUiStore());
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from,
.notification-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

@keyframes loadingDots {
  0% {
    content: ".";
  }
  33% {
    content: "..";
  }
  66% {
    content: "...";
  }
}

.loading-dots {
  display: inline-block;
  width: 16px;
}

.loading-dots::after {
  content: "";
  animation: loadingDots 1.5s infinite;
}
</style>
