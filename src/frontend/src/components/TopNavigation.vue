<template>
  <nav class="fixed top-0 left-0 right-0 bg-surface/95 backdrop-blur-sm z-20 px-8 h-16 border-b border-surface-container">
    <div class="max-w-7xl mx-auto h-full flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary text-2xl">movie</span>
        <span class="font-headline font-bold text-lg">AutoVid</span>
      </router-link>

      <!-- Nav Links -->
      <div class="flex items-center gap-6">
        <router-link
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="text-sm font-medium transition-colors"
          :class="isActive(link.to) ? 'text-primary font-bold' : 'text-on-surface-variant hover:text-on-surface'"
        >
          {{ link.label }}
        </router-link>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-4">
        <router-link
          to="/settings/models"
          class="p-2 hover:bg-surface-container rounded-full transition-colors"
        >
          <span class="material-symbols-outlined text-on-surface-variant">settings</span>
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navLinks = [
  { to: '/projects', label: '项目列表' },
  { to: '/characters', label: '角色库' },
]

const isActive = (path) => {
  return route.path.startsWith(path)
}
</script>
