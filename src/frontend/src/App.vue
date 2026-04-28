<template>
  <div class="min-h-screen bg-surface">
    <TopNavigation />
    <main class="pt-16">
      <router-view />
    </main>
    <BottomNavBar v-if="showBottomNav" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TopNavigation from '@/components/TopNavigation.vue'
import BottomNavBar from '@/components/BottomNavBar.vue'

const route = useRoute()

const showBottomNav = computed(() => {
  const hiddenRoutes = ['/', '/settings', '/characters', '/projects']
  return !hiddenRoutes.some(r => route.path.startsWith(r))
})
</script>
