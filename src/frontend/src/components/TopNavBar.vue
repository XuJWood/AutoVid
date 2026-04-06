<template>
  <header class="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl flex justify-between items-center h-16 px-8">
    <div class="flex items-center gap-8">
      <router-link to="/" class="text-xl font-bold tracking-tight text-primary font-headline">
        AutoVid
      </router-link>
      <nav class="hidden md:flex gap-6">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="text-sm font-medium text-on-surface-variant hover:text-primary transition-colors"
          :class="{ 'text-primary border-b-2 border-primary pb-1': isActive(item.path) }"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </div>
    <div class="flex items-center gap-4">
      <router-link to="/settings/models" class="p-2 text-on-surface-variant hover:text-primary transition-colors">
        <span class="material-symbols-outlined">settings</span>
      </router-link>
      <div class="w-8 h-8 rounded-full bg-primary-container overflow-hidden cursor-pointer">
        <img
          alt="User Avatar"
          class="w-full h-full object-cover"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuB_RpZ6kbI0l-ZMGv1KyFr9eXADErDUeQSeOomeDvxJ7vpOa85AhCcDWZjrFiPsPQ3SV1I9eHpJwS2M_VzR87csc2wKXs4GZQG3dY5ooVN5_sVg8mKgxXdWMgorrGNu-lFVanPjO_yahOwQUXnKENZbu0tZSLVXIYAPNq6tPZ0d8dZXdoMNhZub4uRgn42A8-hB5AqYq1-gdNphiw8DZdlyh9HsaYeVXsho5E1V9gSOmzMeHg15D0rZqSJAj_J0Gh2a0w0nYl0oBX8"
        />
      </div>
    </div>
  </header>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { label: '短剧创作', path: '/drama/create' },
  { label: '视频生成', path: '/video/select' },
  { label: '我的项目', path: '/projects' },
  { label: '角色库', path: '/characters' }
]

const isActive = (path) => {
  return route.path.startsWith(path)
}
</script>
