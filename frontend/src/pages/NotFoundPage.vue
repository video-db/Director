<template>
  <div class="mx-auto flex min-h-full w-full max-w-640 flex-col justify-center px-16 py-40 md:px-24">
    <EmptyState
      icon="explore_off"
      :level="2"
      title="Page not found"
      description="The page you're looking for doesn't exist or has moved."
    >
      <Button :as="RouterLink" :to="{ name: 'home' }" hierarchy="secondary" icon="home">
        Back to home
      </Button>
    </EmptyState>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
</script>
