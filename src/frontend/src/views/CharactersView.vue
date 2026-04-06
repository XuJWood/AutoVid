<template>
  <div class="min-h-screen pt-24 pb-32 px-8 max-w-7xl mx-auto">
    <header class="mb-8 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">我的角色库</h1>
        <p class="text-on-surface-variant">管理您的角色形象，可在多个项目中复用</p>
      </div>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors flex items-center gap-2"
      >
        <span class="material-symbols-outlined text-sm">add</span>
        新建角色
      </button>
    </header>

    <!-- Filters -->
    <div class="flex gap-4 mb-8">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索角色..."
        class="flex-1 bg-surface-container-lowest border-none rounded-lg px-4 py-2 text-sm"
      />
      <select v-model="filterStyle" class="bg-surface-container-lowest border-none rounded-lg px-4 py-2 text-sm">
        <option value="">全部风格</option>
        <option value="realistic">写实风</option>
        <option value="anime">动漫风</option>
        <option value="cinematic">电影质感</option>
      </select>
    </div>

    <!-- Character Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
      <div
        v-for="character in filteredCharacters"
        :key="character.id"
        class="bg-surface-container-lowest rounded-lg overflow-hidden hover:shadow-lg transition-all cursor-pointer group"
      >
        <div class="aspect-[3/4] bg-surface-container relative">
          <img
            v-if="character.selected_image"
            :src="character.selected_image"
            class="w-full h-full object-cover"
          />
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div class="flex gap-2">
              <button class="p-2 bg-white rounded-full">
                <span class="material-symbols-outlined text-primary text-sm">visibility</span>
              </button>
              <button class="p-2 bg-white rounded-full">
                <span class="material-symbols-outlined text-primary text-sm">edit</span>
              </button>
              <button class="p-2 bg-white rounded-full">
                <span class="material-symbols-outlined text-error text-sm">delete</span>
              </button>
            </div>
          </div>
        </div>
        <div class="p-4">
          <h3 class="font-bold text-sm mb-1">{{ character.name }}</h3>
          <p class="text-xs text-on-surface-variant">{{ character.style }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { charactersApi } from '@/api/characters'

const characters = ref([])
const searchQuery = ref('')
const filterStyle = ref('')
const showCreateModal = ref(false)

const filteredCharacters = computed(() => {
  let result = characters.value
  if (searchQuery.value) {
    result = result.filter(c =>
      c.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  if (filterStyle.value) {
    result = result.filter(c => c.style === filterStyle.value)
  }
  return result
})

const loadCharacters = async () => {
  try {
    const response = await charactersApi.getAll()
    characters.value = response.data
  } catch (error) {
    console.error('Failed to load characters:', error)
  }
}

onMounted(loadCharacters)
</script>
