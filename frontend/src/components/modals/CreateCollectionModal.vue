<template>
  <div
    v-if="showDialog"
    class="vdb-c-fixed vdb-c-inset-0 vdb-c-z-50 vdb-c-flex vdb-c-items-center vdb-c-justify-center vdb-c-bg-black/50"
    @click="$emit('cancel')"
  >
    <div
      class="vdb-c-shadow-xl vdb-c-m-10 vdb-c-flex vdb-c-w-[512px] vdb-c-flex-col vdb-c-rounded-lg vdb-c-bg-white"
      @click.stop
    >
      <!-- Modal Content -->
      <div
        class="vdb-c-flex vdb-c-flex-col vdb-c-gap-30 vdb-c-px-30 vdb-c-py-30"
      >
        <!-- Modal Header -->
        <div class="vdb-c-flex vdb-c-items-center vdb-c-gap-10">
          <div
            class="vdb-c-flex vdb-c-h-40 vdb-c-w-40 vdb-c-items-center vdb-c-justify-center vdb-c-rounded-full vdb-c-bg-[#FFE9D3]"
          >
            <CreateCollectionIcon />
          </div>
          <h2 class="vdb-c-text-lg vdb-c-font-medium vdb-c-text-gray-950">
            New Collection
          </h2>
        </div>

        <!-- Input Fields -->
        <div class="vdb-c-flex vdb-c-flex-col vdb-c-gap-10">
          <input
            id="collectionName"
            v-model="newCollection.name"
            autocomplete="off"
            type="text"
            class="vdb-c-box-border vdb-c-w-full vdb-c-rounded-md vdb-c-border vdb-c-border-gray-300 vdb-c-px-10 vdb-c-py-8 vdb-c-text-sm vdb-c-text-kilvish-900 focus:vdb-c-border-orange-500 focus:vdb-c-outline-none"
            placeholder="Collection Name (required)"
          />
          <textarea
            id="collectionDescription"
            v-model="newCollection.description"
            class="vdb-c-box-border vdb-c-w-full vdb-c-rounded-md vdb-c-border vdb-c-border-gray-300 vdb-c-px-10 vdb-c-py-8 vdb-c-text-sm vdb-c-text-kilvish-900 focus:vdb-c-border-orange-500 focus:vdb-c-outline-none"
            placeholder="Description"
            autocomplete="off"
          ></textarea>
        </div>
      </div>

      <div class="vdb-c-w-full vdb-c-rounded-b-lg vdb-c-bg-gray-50">
        <div
          class="vdb-c-flex vdb-c-items-center vdb-c-justify-end vdb-c-gap-8 vdb-c-px-24 vdb-c-py-12"
        >
          <button
            class="vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-justify-center vdb-c-rounded-md vdb-c-border vdb-c-border-gray-300 vdb-c-bg-white vdb-c-px-16 vdb-c-py-8 vdb-c-text-sm vdb-c-font-medium vdb-c-text-gray-700 hover:vdb-c-bg-gray-200 sm:vdb-c-w-auto"
            @click="$emit('cancel')"
          >
            Cancel
          </button>
          <button
            :disabled="!newCollection.name.trim()"
            :class="[
              'vdb-c-flex vdb-c-w-full vdb-c-items-center vdb-c-justify-center vdb-c-rounded-md vdb-c-px-16 vdb-c-py-8 vdb-c-text-sm vdb-c-font-medium sm:vdb-c-w-auto',
              newCollection.name.trim()
                ? 'vdb-c-bg-[#EC5B16] vdb-c-text-white hover:vdb-c-bg-[#D94E14]'
                : 'cursor-not-allowed vdb-c-bg-[#969696] vdb-c-text-white',
            ]"
            @click="handleCreateCollection"
          >
            Create
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, defineProps, defineEmits } from "vue";
import CreateCollectionIcon from "../icons/CreateCollection.vue";

defineProps({
  showDialog: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["cancel", "create"]);

const newCollection = reactive({
  name: "",
  description: "",
});

const handleCreateCollection = () => {
  if (!newCollection.name.trim()) {
    alert("Collection name cannot be empty.");
    return;
  }
  emit("create", { ...newCollection });

  newCollection.name = "";
  newCollection.description = "";
};
</script>
