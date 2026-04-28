<template>
  <div class="min-h-screen pt-24 pb-32 px-8 max-w-7xl mx-auto">
    <div class="mb-8">
      <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">
        视频生成 - 选择人物
      </h1>
      <p class="text-on-surface-variant">选择一个角色形象作为视频主角</p>
    </div>

    <!-- Step Indicator -->
    <div class="flex items-center gap-4 mb-8">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold">1</div>
        <span class="text-sm font-bold text-primary">选择人物</span>
      </div>
      <div class="w-12 h-0.5 bg-surface-container"></div>
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-surface-container text-on-surface-variant flex items-center justify-center text-sm font-bold">2</div>
        <span class="text-sm text-on-surface-variant">设置场景</span>
      </div>
      <div class="w-12 h-0.5 bg-surface-container"></div>
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-surface-container text-on-surface-variant flex items-center justify-center text-sm font-bold">3</div>
        <span class="text-sm text-on-surface-variant">生成视频</span>
      </div>
    </div>

    <!-- Character Grid -->
    <div class="mb-8">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-bold">我的角色库</h2>
        <div class="flex gap-2">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索角色..."
            class="bg-surface-container-low border-none rounded-full px-4 py-2 text-sm"
          />
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div
          v-for="character in filteredCharacters"
          :key="character.id"
          @click="selectedCharacter = character"
          :class="[
            'relative bg-surface-container-lowest rounded-lg overflow-hidden cursor-pointer transition-all',
            selectedCharacter?.id === character.id
              ? 'ring-2 ring-primary ring-offset-2'
              : 'hover:shadow-lg hover:-translate-y-1'
          ]"
        >
          <div class="aspect-[3/4] bg-surface-container">
            <img
              v-if="character.selected_image"
              :src="character.selected_image"
              class="w-full h-full object-cover"
            />
          </div>
          <div class="p-3">
            <p class="font-bold text-sm">{{ character.name }}</p>
            <p class="text-xs text-on-surface-variant">{{ character.style }}</p>
          </div>
          <div
            v-if="selectedCharacter?.id === character.id"
            class="absolute top-2 right-2 bg-primary text-white p-1 rounded-full"
          >
            <span class="material-symbols-outlined text-sm">check</span>
          </div>
        </div>

        <!-- Upload Card -->
        <div
          @click="showUploadModal = true"
          class="aspect-[3/4] rounded-lg border-2 border-dashed border-outline-variant/30 flex flex-col items-center justify-center text-on-surface-variant hover:bg-surface-container cursor-pointer transition-colors"
        >
          <span class="material-symbols-outlined text-3xl mb-2">add</span>
          <span class="text-xs font-medium">上传新人物</span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-end">
      <router-link
        :to="selectedCharacter ? `/video/scene?character_id=${selectedCharacter.id}` : '#'"
        :class="[
          'px-8 py-3 rounded-full font-bold text-sm flex items-center gap-2 transition-all',
          selectedCharacter
            ? 'bg-primary text-white hover:bg-primary-dim'
            : 'bg-surface-container text-on-surface-variant cursor-not-allowed'
        ]"
      >
        下一步：设置场景
        <span class="material-symbols-outlined">arrow_forward</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { charactersApi } from '@/api/characters'

const characters = ref([])
const selectedCharacter = ref(null)
const searchQuery = ref('')
const showUploadModal = ref(false)

const filteredCharacters = computed(() => {
  if (!searchQuery.value) return characters.value
  return characters.value.filter(c =>
    c.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
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
