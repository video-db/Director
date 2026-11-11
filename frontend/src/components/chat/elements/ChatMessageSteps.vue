<template>
  <div class="vdb-c-flex vdb-c-flex-col vdb-c-gap-16">
    <button
      @click="toggleExpand"
      class="vdb-c-focus:outline-none vdb-c-flex vdb-c-items-center vdb-c-gap-8"
    >
      <ChevronDown
        :class="{ 'vdb-c-rotate-180 vdb-c-transform': isExpanded }"
        :stroke-width="2"
        :stroke-color="'#343E4F'"
      />
      <span class="vdb-c-font-medium vdb-c-text-black">Director's Log</span>
    </button>
    <transition
      enter-active-class="vdb-c-transition-all vdb-c-duration-300 vdb-c-ease-out"
      enter-from-class="vdb-c-transform vdb-c-scale-95 vdb-c-opacity-0"
      enter-to-class="vdb-c-transform vdb-c-scale-100 vdb-c-opacity-100"
      leave-active-class="vdb-c-transition-all vdb-c-duration-300 vdb-c-ease-in"
      leave-from-class="vdb-c-transform vdb-c-scale-100 vdb-c-opacity-100"
      leave-to-class="vdb-c-transform vdb-c-scale-95 vdb-c-opacity-0"
    >
      <div
        v-if="isExpanded"
        class="vdb-c-shadow-sm vdb-c-overflow-hidden vdb-c-rounded-md vdb-c-bg-white"
      >
        <div
          class="vdb-c-flex vdb-c-flex-col vdb-c-gap-12 vdb-c-overflow-y-auto"
        >
          <div
            v-for="(step, index) in displaySteps"
            :key="index"
            class="vdb-c-flex vdb-c-items-center vdb-c-gap-8"
          >
            <span
              class="vdb-c-flex vdb-c-h-20 vdb-c-w-20 vdb-c-items-center vdb-c-justify-center"
            >
              <span
                v-if="index !== displaySteps.length - 1"
                class="vdb-c-text-[#D9D9D9]"
                >|</span
              >
              <div
                v-else
                class="vdb-c-block vdb-c-h-1/2 vdb-c-w-10 vdb-c-rounded-full"
                :class="
                  status === 'progress'
                    ? 'vdb-c-animate-pulse vdb-c-bg-orange-500'
                    : status === 'success'
                      ? 'vdb-c-bg-[#0AA910]'
                      : 'vdb-c-bg-[#0075FF]'
                "
              ></div>
            </span>
            <span
              class="vdb-c-flex-grow"
              :class="{
                'vdb-c-font-semibold vdb-c-text-[#0075FF]':
                  status !== 'success' && index === displaySteps.length - 1,
                'vdb-c-font-semibold vdb-c-text-green':
                  status === 'success' && index === displaySteps.length - 1,
                'vdb-c-font-medium vdb-c-text-kilvish-800': !(
                  status === 'success' && index === displaySteps.length - 1
                ),
              }"
              v-html="
                step.replace(
                  /@(\w+)/g,
                  '<span class=\'vdb-c-text-orange-500\'>@$1</span>',
                )
              "
            >
            </span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import ChevronDown from "../../icons/ChevronDown.vue";

const props = defineProps({
  steps: {
    type: Array,
    default: () => [],
  },
  status: {
    type: String,
    default: "progress",
  },
  expanded: {
    type: Boolean,
    default: false,
  },
});

const isExpanded = ref(props.expanded);

watch(
  () => props.expanded,
  (newValue) => {
    if (!newValue) {
      isExpanded.value = false;
    }
  },
);

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
};

const displaySteps = computed(() => {
  if (props.steps.length === 0) {
    return ["Thinking"];
  }
  if (props.status === "success") {
    return [...props.steps, "Final cut ready!"];
  }
  return props.steps;
});
</script>

<style scoped>
.vdb-c-text-orange-500 {
  color: #f97316;
}
.vdb-c-text-green-500 {
  color: #22c55e;
}
</style>
