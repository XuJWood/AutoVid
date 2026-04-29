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
    <div v-if="filteredCharacters.length > 0" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
      <div
        v-for="character in filteredCharacters"
        :key="character.id"
        class="bg-surface-container-lowest rounded-lg overflow-hidden hover:shadow-lg transition-all group"
      >
        <div class="aspect-[3/4] bg-surface-container relative">
          <img
            v-if="character.selected_image"
            :src="toPlayableUrl(character.selected_image)"
            class="w-full h-full object-cover"
            @error="(e) => e.target.style.display = 'none'"
          />
          <div v-else class="w-full h-full flex items-center justify-center">
            <span class="material-symbols-outlined text-4xl text-on-surface-variant/30">person</span>
          </div>
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div class="flex gap-2">
              <button
                @click.stop="previewCharacter(character)"
                class="p-2 bg-white rounded-full hover:scale-110 transition-transform"
                title="查看大图"
              >
                <span class="material-symbols-outlined text-primary text-sm">visibility</span>
              </button>
              <button
                @click.stop="editCharacter(character)"
                class="p-2 bg-white rounded-full hover:scale-110 transition-transform"
                title="编辑/重新生成"
              >
                <span class="material-symbols-outlined text-primary text-sm">edit</span>
              </button>
              <button
                @click.stop="confirmDeleteCharacter(character)"
                :disabled="deletingId === character.id"
                class="p-2 bg-white rounded-full hover:scale-110 transition-transform disabled:opacity-50"
                title="删除"
              >
                <span class="material-symbols-outlined text-error text-sm">{{ deletingId === character.id ? 'autorenew' : 'delete' }}</span>
              </button>
            </div>
          </div>
        </div>
        <div class="p-4">
          <h3 class="font-bold text-sm mb-1 truncate">{{ character.name }}</h3>
          <p class="text-xs text-on-surface-variant truncate">{{ character.gender || '' }} · {{ character.style || 'anime' }}</p>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-16">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant/30 mb-4">person_off</span>
      <p class="text-lg text-on-surface-variant mb-2">还没有角色</p>
      <p class="text-sm text-on-surface-variant/70">在剧本生成时会自动创建，也可以手动新建</p>
    </div>

    <!-- Preview Modal -->
    <div v-if="previewTarget" class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-8" @click.self="previewTarget = null">
      <div class="bg-surface-container-lowest rounded-lg max-w-3xl w-full overflow-hidden">
        <div class="p-4 border-b border-surface-container flex justify-between items-center">
          <h3 class="font-bold">{{ previewTarget.name }}</h3>
          <button @click="previewTarget = null" class="p-2 hover:bg-surface-container rounded-full">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="p-4 max-h-[80vh] overflow-y-auto">
          <img
            v-if="previewTarget.selected_image"
            :src="toPlayableUrl(previewTarget.selected_image)"
            class="w-full h-auto rounded-lg"
          />
          <div v-else class="aspect-[3/4] flex items-center justify-center text-on-surface-variant">
            暂无形象图
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Dialog -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-8" @click.self="deleteTarget = null">
      <div class="bg-surface-container-lowest rounded-lg max-w-md w-full p-6 shadow-2xl">
        <div class="flex items-start gap-3 mb-4">
          <div class="p-2 bg-error/10 rounded-lg">
            <span class="material-symbols-outlined text-error">warning</span>
          </div>
          <div class="flex-1">
            <h3 class="font-bold text-lg mb-1">确认删除角色</h3>
            <p class="text-sm text-on-surface-variant">即将删除 <strong class="text-on-surface">"{{ deleteTarget.name }}"</strong>，包括三视图、表情图等所有形象资料。</p>
            <p class="text-xs text-on-surface-variant/70 mt-2">提示：删除后该角色在剧本中的台词不受影响，但视频生成时将失去角色一致性参考。</p>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="deleteTarget = null" class="px-4 py-2 text-sm font-bold rounded-full bg-surface-container hover:bg-surface-container-high transition-colors">
            取消
          </button>
          <button
            @click="executeDelete"
            :disabled="deletingId !== null"
            class="px-4 py-2 text-sm font-bold rounded-full bg-error text-white hover:brightness-110 transition-all disabled:opacity-50"
          >
            {{ deletingId !== null ? '删除中...' : '确认删除' }}
          </button>
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
const deleteTarget = ref(null)
const previewTarget = ref(null)
const deletingId = ref(null)

function toPlayableUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/media/')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

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

const previewCharacter = (character) => {
  previewTarget.value = character
}

const editCharacter = (character) => {
  // Navigate to project workspace where character can be re-generated
  if (character.project_id) {
    window.location.href = `/drama/${character.project_id}`
  } else {
    alert('该角色未关联项目，请先打开对应项目编辑')
  }
}

const confirmDeleteCharacter = (character) => {
  deleteTarget.value = character
}

const executeDelete = async () => {
  if (!deleteTarget.value) return
  const id = deleteTarget.value.id
  deletingId.value = id
  try {
    await charactersApi.delete(id)
    characters.value = characters.value.filter(c => c.id !== id)
    deleteTarget.value = null
  } catch (error) {
    console.error('Failed to delete character:', error)
    alert('删除失败：' + (error.response?.data?.detail || error.message))
  } finally {
    deletingId.value = null
  }
}

onMounted(loadCharacters)
</script>
