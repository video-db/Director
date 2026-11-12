<template>
  <div
    class="image-card vdb-c-flex vdb-c-h-full vdb-c-cursor-pointer vdb-c-flex-col vdb-c-rounded-lg vdb-c-bg-kilvish-200 vdb-c-p-6 vdb-c-transition-colors vdb-c-duration-300 hover:vdb-c-bg-white hover:vdb-c-shadow-lg"
  >
    <div
      :class="[
        'vdb-c-flex vdb-c-flex-col sm:vdb-c-block sm:vdb-c-flex-row',
        {
          'vdb-c-mb-14': variant === 'default',
        },
      ]"
    >
      <div
        :class="[
          'sm:vdb-c-min-w-auto sm:vdb-c-min-w-0 vdb-c-w-auto vdb-c-min-w-96 sm:vdb-c-mr-24 sm:vdb-c-w-full',
          {
            'vdb-c-mb-8 sm:vdb-c-mb-16': variant === 'default',
          },
        ]"
      >
        <div
          class="vid-pb vdb-c-relative vdb-c-overflow-hidden vdb-c-rounded-[7px]"
        >
          <div
            v-if="url"
            class="thumbnail vdb-c-absolute vdb-c-bottom-0 vdb-c-left-0 vdb-c-right-0 vdb-c-top-0 vdb-c-h-106 vdb-c-rounded-lg vdb-c-bg-cover vdb-c-bg-center vdb-c-bg-no-repeat vdb-c-shadow-1"
            :style="{
              backgroundImage: `url('${url}')`,
              backgroundColor: 'transparent',
            }"
          ></div>
          <default-thumbnail
            v-else
            class="thumbnail vdb-c-absolute vdb-c-bottom-0 vdb-c-left-0 vdb-c-right-0 vdb-c-top-0 vdb-c-h-106 vdb-c-animate-pulse vdb-c-rounded-lg vdb-c-bg-cover vdb-c-bg-center vdb-c-bg-no-repeat vdb-c-shadow-1"
          />
          <div
            class="vdb-c-absolute vdb-c-right-4 vdb-c-top-4 vdb-c-rounded-full vdb-c-border vdb-c-bg-black/40 vdb-c-p-6 vdb-c-backdrop-blur vdb-c-transition-transform vdb-c-duration-300 hover:vdb-c-scale-110 hover:vdb-c-bg-white/45"
            @click="copyId(item.id)"
          >
            <CopyIcon />
          </div>
        </div>
      </div>
      <div
        v-if="variant === 'default'"
        class="vdb-c-mx-8 vdb-c-mb-8 vdb-c-flex vdb-c-items-center vdb-c-justify-between vdb-c-text-kilvish-900"
      >
        <p
          class="text-elip vdb-c-mb-0 vdb-c-line-clamp-2 vdb-c-whitespace-normal vdb-c-text-xs vdb-c-font-medium"
        >
          {{ item.name }}
        </p>
        <span
          class="vdb-c-ml-4 vdb-c-cursor-pointer vdb-c-transition-all vdb-c-duration-300 hover:vdb-c-scale-110"
          @click.stop="$emit('delete-image', item)"
        >
          <DeleteIcon
            :fill="hoveredDeleteIcon === item.id ? '#EC5B16' : '#CCCCCC'"
          />
        </span>
      </div>
    </div>
  </div>
  <NotificationCenter ref="notificationCenterRef" />
</template>

<script setup>
import { onMounted, ref } from "vue";
import NotificationCenter from "../chat/elements/NotificationCenter.vue";
import CopyIcon from "../icons/CopyIcon.vue";
import DeleteIcon from "../icons/Delete2.vue";

const hoveredDeleteIcon = ref(null);
const url = ref(null);
const props = defineProps({
  item: {
    type: Object,
    default: () => ({}),
  },
  index: {
    type: Number,
    default: 0,
  },
  variant: {
    type: String,
    default: "default",
  },
  getImageUrl: {
    type: Function,
  },
});

onMounted(async () => {
  if (props.getImageUrl) {
    const imageUrl = await props.getImageUrl(
      props.item.collection_id,
      props.item.id,
    );
    url.value = imageUrl.url;
  }
});

const notificationCenterRef = ref(null);

function copyId(id) {
  navigator.clipboard
    .writeText(id)
    .then(() => {
      notificationCenterRef.value.addNotification("Image ID Copied");
    })
    .catch(() => {
      notificationCenterRef.value.addNotification("Failed to copy ID");
    });
}

const emit = defineEmits(["delete-image"]);
</script>

<style scoped>
.transparent-button {
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.24);
  backdrop-filter: blur(16px);
  color: #fff;
  opacity: 0;
}

.vid-pb {
  padding-bottom: 56.25%;
}

.text-elip {
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.center-button,
.fade-on-hover {
  transition: all 0.3s ease-in-out;
}
.thumbnail {
  transition: transform 0.5s linear;
  transform-origin: center;
  transform: scale(1.001);
}
@media (max-width: 640px) {
  .thumbnail {
    height: 106px;
  }
  .vid-pb {
    padding-bottom: 40%;
  }
}

@media (any-hover: hover) {
  .image-card:hover .center-button {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.05);
    background: rgba(0, 0, 0, 0.32);
    transform-origin: center;
  }
  .image-card:hover .fade-on-hover {
    opacity: 0.6;
  }
  .image-card:hover .thumbnail {
    transform: scale(1.05);
  }
}
</style>
