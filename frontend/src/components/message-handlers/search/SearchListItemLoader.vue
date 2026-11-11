<template>
  <div class="vdb-c-flex vdb-c-flex-col vdb-c-gap-24">
    <div
      v-for="(searchItem, index) in getArr()"
      :key="`search-results-${index}`"
      class="vdb-c-flex vdb-c-flex-col md:vdb-c-grid md:vdb-c-grid-cols-12 vdb-c-gap-24 vdb-c-border-b vdb-c-border-outline-xlight vdb-c-py-24"
    >
      <div class="vdb-c-w-full md:vdb-c-col-span-3">
        <div class="vdb-c-flex vdb-c-h-full vdb-c-flex-col">
          <div class="vdb-c-flex vdb-c-flex-col vdb-c-gap-24">
            <div class="vdb-c-mr-24 vdb-c-w-full vdb-c-min-w-96">
              <div
                class="vdb-c-custom-duration vdb-c-relative vdb-c-animate-pulse vdb-c-rounded-12 vdb-c-bg-gray-400"
                style="padding-bottom: 56.25%"
              />
            </div>
            <div class="vdb-c-flex vdb-c-flex-col vdb-c-justify-center">
              <div
                class="vdb-c-custom-duration vdb-c-mb-8 vdb-c-h-20 vdb-c-animate-pulse vdb-c-rounded-full vdb-c-bg-gray-400"
              />
              <div class="vdb-c-flex vdb-c-items-center">
                <div
                  class="vdb-c-custom-duration vdb-c-mr-12 vdb-c-h-20 vdb-c-w-48 vdb-c-animate-pulse vdb-c-rounded-full vdb-c-bg-gray-400"
                />
                <div
                  class="vdb-c-custom-duration vdb-c-h-20 vdb-c-w-48 vdb-c-animate-pulse vdb-c-rounded-full vdb-c-bg-gray-400"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="vdb-c-w-full md:vdb-c-col-span-9">
        <div
          class="vdb-c-custom-duration vdb-c-relative vdb-c-animate-pulse vdb-c-rounded-16 vdb-c-bg-gray-400"
        >
          <div class="vdb-c-h-152 vdb-c-rounded-16 vdb-c-bg-gray-400" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "SearchListItemLoader",
  props: {
    limit: {
      type: Number,
      default: 1,
    },
  },
  methods: {
    getArr() {
      const arr = [];
      for (let i = 0; i < this.limit; i++) {
        arr.push(i + 1);
      }
      return arr;
    },
  },
};
</script>
