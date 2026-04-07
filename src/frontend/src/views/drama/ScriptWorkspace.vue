<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto grid grid-cols-12 gap-8">
      <!-- Left: Character Panel -->
      <aside class="col-span-12 lg:col-span-3 flex flex-col gap-6">
        <div class="flex justify-between items-end">
          <h2 class="text-xl font-bold font-headline tracking-tight">角色设定</h2>
          <button @click="showAddCharacter = true" class="text-xs text-primary font-bold">+ 添加角色</button>
        </div>
        <div class="bg-surface-container-low rounded-lg p-6 flex-1 overflow-y-auto custom-scrollbar">
          <div class="space-y-4">
            <div
              v-for="character in characters"
              :key="character.id"
              class="bg-surface-container-lowest rounded-lg p-4 border border-primary/10"
            >
              <div class="flex items-center gap-4">
                <div class="w-16 h-20 bg-surface-container rounded-lg overflow-hidden">
                  <img
                    v-if="character.selected_image"
                    :src="character.selected_image"
                    class="w-full h-full object-cover"
                  />
                  <span v-else class="material-symbols-outlined text-3xl text-on-surface-variant">person</span>
                </div>
                <div class="flex-1">
                  <h4 class="font-bold text-sm">{{ character.name }}</h4>
                  <p class="text-xs text-on-surface-variant">{{ character.age }}岁 · {{ character.occupation }}</p>
                </div>
              </div>
              <div class="flex gap-2 mt-4">
                <button
                  @click="openCharacterModal(character)"
                  class="flex-1 py-2 text-xs font-bold bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors"
                >
                  生成形象
                </button>
                <button
                  @click="editCharacter(character)"
                  class="px-3 py-2 text-xs bg-surface-container text-on-surface-variant rounded-lg hover:bg-surface-container-high transition-colors"
                >
                  <span class="material-symbols-outlined text-sm">edit</span>
                </button>
              </div>
            </div>

            <button
              @click="showAddCharacter = true"
              class="w-full py-4 border-2 border-dashed border-outline-variant/30 rounded-lg text-on-surface-variant hover:bg-surface-container transition-colors"
            >
              <span class="material-symbols-outlined">add</span>
              <span class="text-xs">添加角色</span>
            </button>
          </div>
        </div>
      </aside>

      <!-- Right: Script Editor -->
      <section class="col-span-12 lg:col-span-9 flex flex-col gap-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold font-headline tracking-tight">剧本内容</h2>
            <p class="text-sm text-on-surface-variant">编辑剧本结构、场景和镜头</p>
          </div>
          <div class="flex gap-2">
            <button
              @click="generateScript"
              :disabled="generating"
              class="flex items-center gap-2 bg-primary-container text-on-primary-container px-4 py-2 rounded-full text-xs font-bold hover:brightness-95 transition-all disabled:opacity-50"
            >
              <span class="material-symbols-outlined text-sm">auto_awesome</span>
              {{ generating ? '生成中...' : '生成剧本' }}
            </button>
            <router-link
              v-if="scriptContent?.scenes"
              :to="`/drama/${projectId}/storyboard`"
              class="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-full text-xs font-bold hover:brightness-95 transition-all"
            >
              <span class="material-symbols-outlined text-sm">movie</span>
              进入分镜
            </router-link>
          </div>
        </div>

        <!-- 额外提示词输入 -->
        <div v-if="!generating && !scriptContent?.scenes" class="bg-surface-container-low rounded-lg p-4">
          <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-2 block">
            额外创作要求（可选）
          </label>
          <textarea
            v-model="customPrompt"
            rows="2"
            class="w-full bg-surface-container-lowest border-none rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50"
            placeholder="例如：加入反转情节、增加职场元素、角色要有更多互动..."
          ></textarea>
        </div>

        <!-- 生成进度显示 -->
        <div v-if="generating" class="bg-primary/10 rounded-lg p-6">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary animate-spin">autorenew</span>
            </div>
            <div class="flex-1">
              <h4 class="font-bold text-primary">{{ progressMessage }}</h4>
              <div class="w-full bg-surface-container-high rounded-full h-2 mt-2">
                <div
                  class="bg-primary h-2 rounded-full transition-all duration-300"
                  :style="{ width: progress + '%' }"
                ></div>
              </div>
            </div>
            <span class="text-sm font-bold text-primary">{{ progress }}%</span>
          </div>
        </div>

        <!-- 生成结果消息 -->
        <div v-if="resultMessage && !generating" class="rounded-lg p-4" :class="resultSuccess ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined">{{ resultSuccess ? 'check_circle' : 'warning' }}</span>
            <span class="text-sm font-medium">{{ resultMessage }}</span>
          </div>
        </div>

        <!-- Script Content -->
        <div class="bg-surface-container-lowest rounded-lg p-8 shadow-sm flex-1">
          <div v-if="scriptContent && scriptContent.scenes" class="space-y-6">
            <!-- 剧本标题和简介 -->
            <div class="border-b border-surface-container pb-4">
              <h3 class="text-2xl font-bold font-headline">{{ scriptContent.title }}</h3>
              <p v-if="scriptContent.logline" class="text-on-surface-variant mt-2 italic">{{ scriptContent.logline }}</p>
            </div>

            <!-- 角色列表 -->
            <div v-if="scriptContent.characters && scriptContent.characters.length > 0" class="border-b border-surface-container pb-4">
              <h4 class="font-bold text-sm text-on-surface-variant mb-3 uppercase tracking-wider">主要角色</h4>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div
                  v-for="char in scriptContent.characters"
                  :key="char.name"
                  class="bg-surface-container-low p-3 rounded-lg"
                >
                  <div class="font-bold text-sm">{{ char.name }}</div>
                  <div class="text-xs text-on-surface-variant">{{ char.age }}岁 · {{ char.occupation || '未知' }}</div>
                  <div v-if="char.personality" class="text-xs text-on-surface-variant mt-1">{{ char.personality }}</div>
                </div>
              </div>
            </div>

            <!-- 场景列表 -->
            <div v-for="scene in scriptContent.scenes" :key="scene.id" class="border-b border-surface-container pb-6 last:border-0">
              <h3 class="font-bold text-lg mb-2 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">scene</span>
                {{ scene.name }}
              </h3>
              <p class="text-sm text-on-surface-variant mb-4">
                📍 {{ scene.environment }}
                <span v-if="scene.time"> · 🕐 {{ scene.time }}</span>
                <span v-if="scene.mood"> · 🎭 {{ scene.mood }}</span>
              </p>

              <div class="space-y-3">
                <div
                  v-for="shot in scene.shots"
                  :key="shot.id"
                  class="bg-surface-container-low p-4 rounded-lg"
                >
                  <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded">{{ shot.type }}</span>
                      <span v-if="shot.movement" class="text-xs text-on-surface-variant">{{ shot.movement }}</span>
                    </div>
                    <span class="text-xs font-bold text-on-surface-variant">{{ shot.duration }}s</span>
                  </div>
                  <p class="text-sm mb-2">{{ shot.description }}</p>
                  <p v-if="shot.dialogue" class="text-sm text-primary-container bg-primary/5 p-2 rounded italic">"{{ shot.dialogue }}"</p>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="text-center py-16 text-on-surface-variant">
            <span class="material-symbols-outlined text-6xl mb-4 opacity-50">description</span>
            <p class="text-lg">还没有剧本内容</p>
            <p class="text-sm">点击"生成剧本"开始创作</p>
          </div>
        </div>
      </section>
    </div>

    <!-- Character Modal -->
    <CharacterModal
      v-if="showCharacterModal"
      :character="selectedCharacter"
      @close="showCharacterModal = false"
      @select="onCharacterImageSelect"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi } from '@/api/projects'
import { charactersApi } from '@/api/characters'
import CharacterModal from '@/components/CharacterModal.vue'

const route = useRoute()
const projectId = route.params.id

const project = ref(null)
const characters = ref([])
const scriptContent = ref(null)
const generating = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const resultMessage = ref('')
const resultSuccess = ref(true)
const customPrompt = ref('')
const showCharacterModal = ref(false)
const showAddCharacter = ref(false)
const selectedCharacter = ref(null)

const loadProject = async () => {
  try {
    const [projectRes, charactersRes] = await Promise.all([
      projectsApi.get(projectId),
      projectsApi.getCharacters(projectId)
    ])
    project.value = projectRes.data
    characters.value = charactersRes.data
    scriptContent.value = projectRes.data.script_content
  } catch (error) {
    console.error('Failed to load project:', error)
  }
}

const generateScript = async () => {
  generating.value = true
  progress.value = 0
  progressMessage.value = '正在准备...'
  resultMessage.value = ''

  try {
    // 使用 fetch 处理流式响应
    const response = await fetch(`http://127.0.0.1:8000/api/v1/projects/${projectId}/script/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        input: project.value?.description || '',
        prompt_suffix: customPrompt.value
      })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.progress !== undefined) {
              progress.value = data.progress
            }
            if (data.message) {
              progressMessage.value = data.message
            }
            if (data.status === 'completed') {
              scriptContent.value = data.script
              resultMessage.value = data.message
              resultSuccess.value = data.message.includes('成功')
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  } catch (error) {
    console.error('Failed to generate script:', error)
    resultMessage.value = '生成失败：' + error.message
    resultSuccess.value = false
  } finally {
    generating.value = false
  }
}

const openCharacterModal = (character) => {
  selectedCharacter.value = character
  showCharacterModal.value = true
}

const editCharacter = (character) => {
  selectedCharacter.value = character
  showCharacterModal.value = true
}

const onCharacterImageSelect = async ({ characterId, imageUrl }) => {
  try {
    await charactersApi.selectImage(characterId, imageUrl)
    loadProject()
  } catch (error) {
    console.error('Failed to select image:', error)
  }
}

onMounted(loadProject)
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
