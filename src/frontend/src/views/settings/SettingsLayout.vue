<template>
  <div class="min-h-screen pt-16 flex">
    <!-- Sidebar -->
    <aside class="h-screen w-64 border-r border-on-surface-variant/10 bg-surface-container-low flex flex-col py-6 px-4 gap-2 shrink-0">
      <div class="mb-6 px-2">
        <h2 class="text-lg font-semibold text-primary font-headline">设置中心</h2>
        <p class="text-xs text-on-surface-variant opacity-70">管理您的AI偏好</p>
      </div>
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex items-center gap-3 px-4 py-3 text-sm rounded-xl transition-all',
          isActive(item.path)
            ? 'bg-white text-primary font-bold translate-x-1'
            : 'text-on-surface-variant hover:bg-white/50'
        ]"
      >
        <span class="material-symbols-outlined">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </router-link>
    </aside>

    <!-- Content -->
    <main class="flex-1 overflow-y-auto bg-surface p-8 pb-32">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const menuItems = [
  { label: '模型配置', path: '/settings/models', icon: 'settings_input_component' },
  { label: '提示词模板', path: '/settings/prompts', icon: 'terminal' },
  { label: '默认设置', path: '/settings/defaults', icon: 'tune' }
]

const isActive = (path) => {
  return route.path === path
}
</script>
