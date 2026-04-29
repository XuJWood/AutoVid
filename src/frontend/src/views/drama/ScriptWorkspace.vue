<template>
  <div class="min-h-screen pt-24 pb-32 px-8">
    <div class="max-w-[1600px] mx-auto grid grid-cols-12 gap-8">
      <!-- Left: Character Panel -->
      <aside class="col-span-12 lg:col-span-3 flex flex-col gap-6">
        <div class="flex justify-between items-end">
          <h2 class="text-xl font-bold font-headline tracking-tight">角色设定</h2>
          <span class="text-xs text-on-surface-variant">{{ characters.length }} 个角色</span>
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
                    :src="toPlayableUrl(character.selected_image)"
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
                  title="编辑"
                >
                  <span class="material-symbols-outlined text-sm">edit</span>
                </button>
                <button
                  @click="confirmDeleteCharacter(character)"
                  :disabled="deletingCharId === character.id"
                  class="px-3 py-2 text-xs bg-error/10 text-error rounded-lg hover:bg-error/20 transition-colors disabled:opacity-50"
                  title="删除角色"
                >
                  <span class="material-symbols-outlined text-sm">{{ deletingCharId === character.id ? 'autorenew' : 'delete' }}</span>
                </button>
              </div>
            </div>

            <p class="text-xs text-center text-on-surface-variant/50 py-4">
              角色由剧本生成时自动创建
            </p>
          </div>
        </div>
      </aside>

      <!-- Right: Script Editor -->
      <section class="col-span-12 lg:col-span-9 flex flex-col gap-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold font-headline tracking-tight">剧本内容</h2>
            <p class="text-sm text-on-surface-variant">编辑剧本结构、剧集和对话</p>
          </div>
          <div class="flex gap-2">
            <button
              v-if="isEditing"
              @click="saveScript"
              :disabled="saving"
              class="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-full text-xs font-bold hover:brightness-95 transition-all disabled:opacity-50"
            >
              <span class="material-symbols-outlined text-sm">save</span>
              {{ saving ? '保存中...' : '保存剧本' }}
            </button>
            <button
              @click="toggleEdit"
              class="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-full text-xs font-bold hover:bg-surface-container-high transition-all"
            >
              <span class="material-symbols-outlined text-sm">{{ isEditing ? 'close' : 'edit' }}</span>
              {{ isEditing ? '取消编辑' : '编辑剧本' }}
            </button>
            <button
              @click="generateScript"
              :disabled="generating"
              class="flex items-center gap-2 bg-primary-container text-on-primary-container px-4 py-2 rounded-full text-xs font-bold hover:brightness-95 transition-all disabled:opacity-50"
            >
              <span class="material-symbols-outlined text-sm">auto_awesome</span>
              {{ generating ? '生成中...' : '生成剧本' }}
            </button>
            <router-link
              v-if="scriptContent?.episodes || scriptContent?.scenes"
              :to="`/drama/${projectId}/storyboard`"
              class="flex items-center gap-2 bg-primary text-on-primary px-4 py-2 rounded-full text-xs font-bold hover:brightness-95 transition-all"
            >
              <span class="material-symbols-outlined text-sm">movie</span>
              编辑剧集
            </router-link>
          </div>
        </div>

        <!-- 集数规模 -->
        <div v-if="!generating && !scriptContent?.episodes && !scriptContent?.scenes" class="bg-surface-container-low rounded-lg p-4">
          <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-2 block">
            集数规模
          </label>
          <select v-model="episodeTier" class="w-full bg-surface-container-lowest border-none rounded-lg p-3 text-sm mb-4">
            <option value="short">短篇 (8-20集)</option>
            <option value="medium">中篇 (20-50集)</option>
            <option value="long">长篇 (80-120集)</option>
          </select>

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
              <div class="flex items-center gap-2 mt-1">
                <span
                  v-for="stage in progressStages"
                  :key="stage.key"
                  class="text-xs px-2 py-0.5 rounded-full transition-colors"
                  :class="stage.done ? 'bg-primary text-on-primary' : stage.active ? 'bg-primary/20 text-primary' : 'bg-surface-container-high text-on-surface-variant/50'"
                >
                  {{ stage.label }}
                </span>
              </div>
              <div class="w-full bg-surface-container-high rounded-full h-2 mt-2">
                <div
                  class="bg-primary h-2 rounded-full transition-all duration-500"
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
        <div v-if="loading" class="bg-surface-container-lowest rounded-lg p-12 text-center">
          <span class="material-symbols-outlined text-4xl text-primary animate-spin mb-3">autorenew</span>
          <p class="text-sm text-on-surface-variant">正在加载项目数据...</p>
        </div>
        <div v-else-if="scriptContent && (scriptContent.episodes || scriptContent.scenes)" class="bg-surface-container-lowest rounded-lg p-8 shadow-sm flex-1">
            <!-- 剧本标题和简介（可编辑） -->
            <div class="border-b border-surface-container pb-4">
              <template v-if="isEditing">
                <input v-model="editableScript.title" class="w-full text-2xl font-bold font-headline bg-surface-container-low rounded px-2 py-1 mb-2 border border-surface-container focus:outline-none focus:border-primary" />
                <textarea v-model="editableScript.logline" rows="2" class="w-full text-on-surface-variant bg-surface-container-low rounded px-2 py-1 italic text-sm border border-surface-container focus:outline-none focus:border-primary"></textarea>
                <div class="flex gap-4 mt-2">
                  <label class="text-xs text-on-surface-variant">画风：<input v-model="editableScript.art_style" class="bg-surface-container-low rounded px-2 py-1 border border-surface-container text-sm w-64" placeholder="日系动漫风，二次元" /></label>
                  <label class="text-xs text-on-surface-variant">总时长：<input v-model.number="editableScript.total_duration" type="number" class="bg-surface-container-low rounded px-2 py-1 border border-surface-container text-sm w-20" />s</label>
                </div>
              </template>
              <template v-else>
                <h3 class="text-2xl font-bold font-headline">{{ scriptContent.title }}</h3>
                <p v-if="scriptContent.logline" class="text-on-surface-variant mt-2 italic">{{ scriptContent.logline }}</p>
                <p v-if="scriptContent.art_style" class="text-xs text-on-surface-variant mt-1">{{ scriptContent.art_style }}</p>
              </template>
            </div>

            <!-- 角色列表 -->
            <div v-if="scriptContent.characters && scriptContent.characters.length > 0" class="border-b border-surface-container pb-4">
              <div class="flex items-center justify-between mb-3">
                <h4 class="font-bold text-sm text-on-surface-variant uppercase tracking-wider">主要角色</h4>
                <button
                  @click="showDialogueDrawer = true"
                  class="text-xs font-bold text-primary flex items-center gap-1 hover:underline"
                >
                  <span class="material-symbols-outlined text-sm">forum</span>
                  查看全部对话
                </button>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div
                  v-for="char in scriptContent.characters"
                  :key="char.name"
                  class="bg-surface-container-low p-3 rounded-lg"
                >
                  <div class="font-bold text-sm">{{ char.name }}</div>
                  <div class="text-xs text-on-surface-variant">{{ char.age }}岁 · {{ char.occupation || '未知' }}</div>
                  <div v-if="char.personality" class="text-xs text-on-surface-variant mt-1">{{ typeof char.personality === 'string' ? char.personality : char.personality?.traits?.join('、') }}</div>
                </div>
              </div>
            </div>

            <!-- 剧集列表（优先 episodes，回退 scenes） -->
            <div v-for="(ep, epIdx) in episodes" :key="ep.episode_number || ep.id" class="border-b border-surface-container pb-6 last:border-0">
              <h3 class="font-bold text-lg mb-2 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">movie</span>
                第{{ ep.episode_number || ep.id }}集：{{ isEditing ? '' : (ep.title || '未命名') }}
                <input v-if="isEditing" v-model="ep.title" class="bg-surface-container-low rounded px-2 py-1 border border-surface-container text-sm flex-1 focus:outline-none focus:border-primary" />
              </h3>
              <p class="text-sm text-on-surface-variant mb-2">
                {{ ep.environment || ep.location }}
                <span v-if="ep.time"> · {{ ep.time }}</span>
                <span v-if="ep.mood"> · {{ ep.mood }}</span>
                <span class="ml-2 text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">{{ ep.duration || 60 }}s</span>
              </p>
              <p class="text-sm mb-3 text-on-surface-variant">{{ ep.description }}</p>

              <!-- 对话预览 -->
              <div v-if="ep.dialogues && ep.dialogues.length > 0" class="bg-primary/5 rounded-lg p-3 mb-3">
                <p class="text-xs font-bold text-on-surface-variant mb-2 uppercase tracking-wider">对话</p>
                <div class="space-y-1">
                  <div v-for="(d, dIdx) in ep.dialogues" :key="dIdx" class="text-sm">
                    <template v-if="isEditing">
                      <div class="flex gap-2 mb-1">
                        <input v-model="d.speaker" class="bg-surface-container-low rounded px-2 py-0.5 border border-surface-container text-xs w-20 focus:outline-none focus:border-primary" placeholder="角色" />
                        <input v-model="d.text" class="bg-surface-container-low rounded px-2 py-0.5 border border-surface-container text-xs flex-1 focus:outline-none focus:border-primary" placeholder="台词" />
                        <input v-model="d.emotion" class="bg-surface-container-low rounded px-2 py-0.5 border border-surface-container text-xs w-16 focus:outline-none focus:border-primary" placeholder="情绪" />
                      </div>
                    </template>
                    <template v-else>
                      <span class="text-primary font-bold">{{ d.speaker }}</span><span v-if="d.speaker">：</span><span class="text-on-surface">{{ d.text }}</span>
                      <span v-if="d.emotion" class="text-xs text-on-surface-variant ml-2">({{ d.emotion }})</span>
                    </template>
                  </div>
                </div>
              </div>

              <!-- Segments (片段列表) -->
              <div v-if="ep.segments && ep.segments.length > 0" class="space-y-2">
                <p class="text-xs font-bold text-on-surface-variant mb-2 uppercase tracking-wider">片段 ({{ ep.segments.length }}段)</p>
                <div
                  v-for="seg in ep.segments"
                  :key="seg.segment_number"
                  class="bg-surface-container-low p-3 rounded-lg border-l-2 border-primary/30"
                >
                  <div class="flex items-center justify-between mb-1">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">段{{ seg.segment_number }}</span>
                      <span v-if="seg.camera_movement" class="text-xs text-on-surface-variant flex items-center gap-1">
                        <span class="material-symbols-outlined text-xs">videocam</span>
                        {{ seg.camera_movement }}
                      </span>
                    </div>
                    <span class="text-xs font-bold text-on-surface-variant">{{ seg.duration || 15 }}s</span>
                  </div>
                  <p class="text-xs mb-1 leading-relaxed">{{ seg.visual_description }}</p>
                  <p v-if="seg.dialogue" class="text-xs text-primary bg-primary/5 p-2 rounded italic mt-1">
                    <span class="material-symbols-outlined text-xs align-middle">record_voice_over</span>
                    {{ seg.dialogue }}
                  </p>
                </div>
              </div>
              <!-- Fallback: shots (old format) -->
              <div v-else-if="ep.shots && ep.shots.length > 0" class="space-y-2">
                <p class="text-xs font-bold text-on-surface-variant mb-2 uppercase tracking-wider">镜头 (旧格式)</p>
                <div
                  v-for="shot in ep.shots"
                  :key="shot.id"
                  class="bg-surface-container-low p-3 rounded-lg"
                >
                  <div class="flex items-center justify-between mb-1">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">{{ shot.type }}</span>
                      <span v-if="shot.movement" class="text-xs text-on-surface-variant">{{ shot.movement }}</span>
                    </div>
                    <span class="text-xs font-bold text-on-surface-variant">{{ shot.duration }}s</span>
                  </div>
                  <p class="text-xs mb-1">{{ shot.description }}</p>
                  <p v-if="shot.dialogue" class="text-xs text-primary-container bg-primary/5 p-2 rounded italic">{{ shot.dialogue }}</p>
                </div>
              </div>
            </div>
          </div>

        <div v-else class="bg-surface-container-lowest rounded-lg p-12 text-center">
          <span class="material-symbols-outlined text-6xl mb-4 opacity-50">description</span>
          <p class="text-lg">还没有剧本内容</p>
          <p class="text-sm">点击"生成剧本"开始创作日系动漫短剧</p>
        </div>
      </section>
    </div>

    <!-- 对话抽屉 (右侧滑出) -->
    <div
      v-if="showDialogueDrawer"
      class="fixed inset-0 z-50 flex justify-end"
    >
      <div class="absolute inset-0 bg-black/40" @click="showDialogueDrawer = false"></div>
      <div class="relative w-full max-w-md bg-surface-container-lowest h-full overflow-y-auto shadow-2xl border-l border-surface-container">
        <div class="sticky top-0 bg-surface-container-lowest border-b border-surface-container p-6 flex items-center justify-between z-10">
          <div>
            <h2 class="text-lg font-bold font-headline">对话面板</h2>
            <p class="text-xs text-on-surface-variant mt-0.5">{{ totalDialogueCount }} 句台词 · {{ episodes.length }} 集</p>
          </div>
          <button @click="showDialogueDrawer = false" class="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center hover:bg-surface-container-high transition-colors">
            <span class="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div v-if="!episodes.length" class="text-center py-12">
            <span class="material-symbols-outlined text-4xl opacity-30 mb-3">forum</span>
            <p class="text-sm text-on-surface-variant">暂无对话数据</p>
          </div>
          <div v-for="ep in episodes" :key="ep.episode_number || ep.id" class="border-b border-surface-container pb-4 last:border-0">
            <h4 class="text-sm font-bold text-primary mb-3 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-base">movie</span>
              第{{ ep.episode_number || ep.id }}集 · {{ ep.title || '未命名' }}
            </h4>
            <div v-if="ep.dialogues && ep.dialogues.length > 0" class="space-y-2">
              <div
                v-for="(d, dIdx) in ep.dialogues"
                :key="dIdx"
                class="bg-surface-container-low rounded-lg p-3"
              >
                <div class="flex items-center gap-2 mb-1.5">
                  <span class="text-xs font-bold text-primary">{{ d.speaker }}</span>
                  <span v-if="d.emotion" class="text-xs text-on-surface-variant bg-surface-container-high px-1.5 py-0.5 rounded-full">{{ d.emotion }}</span>
                </div>
                <p class="text-sm text-on-surface leading-relaxed">{{ d.text }}</p>
              </div>
            </div>
            <p v-else class="text-xs text-on-surface-variant/50">暂无对话</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Character Modal -->
    <CharacterModal
      v-if="showCharacterModal"
      :character="selectedCharacter"
      @close="showCharacterModal = false"
      @select="onCharacterImageSelect"
    />

    <!-- Delete Character Confirm Dialog -->
    <div v-if="deleteCharTarget" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-8" @click.self="deleteCharTarget = null">
      <div class="bg-surface-container-lowest rounded-lg max-w-md w-full p-6 shadow-2xl">
        <div class="flex items-start gap-3 mb-4">
          <div class="p-2 bg-error/10 rounded-lg">
            <span class="material-symbols-outlined text-error">warning</span>
          </div>
          <div class="flex-1">
            <h3 class="font-bold text-lg mb-1">确认删除角色</h3>
            <p class="text-sm text-on-surface-variant">即将删除 <strong class="text-on-surface">"{{ deleteCharTarget.name }}"</strong>，三视图和表情图都会被清空。</p>
            <p class="text-xs text-on-surface-variant/70 mt-2">提示：剧本里的台词不受影响，但视频生成时将失去该角色的形象一致性。</p>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="deleteCharTarget = null" class="px-4 py-2 text-sm font-bold rounded-full bg-surface-container hover:bg-surface-container-high transition-colors">
            取消
          </button>
          <button
            @click="executeDeleteCharacter"
            :disabled="deletingCharId !== null"
            class="px-4 py-2 text-sm font-bold rounded-full bg-error text-white hover:brightness-110 transition-all disabled:opacity-50"
          >
            {{ deletingCharId !== null ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
const progressStages = ref([
  { key: 'prepare', label: '准备提示词', done: false, active: false },
  { key: 'generate', label: 'AI创作中', done: false, active: false },
  { key: 'parse', label: '解析剧本', done: false, active: false },
  { key: 'save', label: '保存数据', done: false, active: false }
])
const resultMessage = ref('')
const resultSuccess = ref(true)
const customPrompt = ref('')
const episodeTier = ref('short')
const showCharacterModal = ref(false)
const selectedCharacter = ref(null)
const deleteCharTarget = ref(null)
const deletingCharId = ref(null)
const loading = ref(true)
const isEditing = ref(false)
const saving = ref(false)
const editableScript = ref(null)
const showDialogueDrawer = ref(false)

function toPlayableUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

// 优先 episodes，回退 scenes
const episodes = computed(() => {
  if (!scriptContent.value) return []
  return scriptContent.value.episodes || scriptContent.value.scenes || []
})

const totalDialogueCount = computed(() => {
  let count = 0
  for (const ep of episodes.value) {
    if (ep.dialogues) count += ep.dialogues.length
  }
  return count
})

const updateStage = (stageKey) => {
  let found = false
  for (const stage of progressStages.value) {
    if (stage.key === stageKey) {
      stage.active = true
      found = true
    } else if (!found) {
      stage.done = true
      stage.active = false
    } else {
      stage.active = false
    }
  }
}

const loadProject = async () => {
  loading.value = true
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
  } finally {
    loading.value = false
  }
}

const toggleEdit = () => {
  if (isEditing.value) {
    isEditing.value = false
    editableScript.value = null
  } else {
    editableScript.value = JSON.parse(JSON.stringify(scriptContent.value || {}))
    if (!editableScript.value.episodes && editableScript.value.scenes) {
      editableScript.value.episodes = editableScript.value.scenes
    }
    isEditing.value = true
  }
}

const saveScript = async () => {
  saving.value = true
  try {
    // 将 episodes 同步回 script_content
    const toSave = { ...editableScript.value }
    // 如果有旧的 scenes 键，用 episodes 替代
    if (toSave.scenes && toSave.episodes) {
      delete toSave.scenes
    }
    await projectsApi.update(projectId, { script_content: toSave })
    scriptContent.value = toSave
    isEditing.value = false
    editableScript.value = null
    resultMessage.value = '剧本已保存'
    resultSuccess.value = true
    setTimeout(() => { resultMessage.value = '' }, 2000)
  } catch (error) {
    console.error('Failed to save script:', error)
    resultMessage.value = '保存失败：' + error.message
    resultSuccess.value = false
  } finally {
    saving.value = false
  }
}

const generateScript = async () => {
  generating.value = true
  progress.value = 0
  progressMessage.value = '正在准备提示词...'
  resultMessage.value = ''
  for (const s of progressStages.value) { s.done = false; s.active = false }
  progressStages.value[0].active = true

  try {
    const response = await fetch(`/api/v1/projects/${projectId}/script/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input: project.value?.description || '',
        prompt_suffix: customPrompt.value,
        episode_tier: episodeTier.value
      })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

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
            if (data.status === 'starting' || data.progress < 20) {
              updateStage('prepare')
            } else if (data.status === 'generating' || (data.progress >= 20 && data.progress < 80)) {
              updateStage('generate')
            } else if (data.progress >= 80 && data.progress < 100) {
              updateStage('parse')
            }

            if (data.status === 'completed' || data.progress >= 100) {
              updateStage('save')
              if (data.script) {
                scriptContent.value = data.script
              }
              if (data.message) {
                resultMessage.value = data.message
                resultSuccess.value = data.status === 'completed'
              }
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

const confirmDeleteCharacter = (character) => {
  deleteCharTarget.value = character
}

const executeDeleteCharacter = async () => {
  if (!deleteCharTarget.value) return
  const id = deleteCharTarget.value.id
  deletingCharId.value = id
  try {
    await charactersApi.delete(id)
    characters.value = characters.value.filter(c => c.id !== id)
    deleteCharTarget.value = null
  } catch (error) {
    console.error('Failed to delete character:', error)
    alert('删除失败：' + (error.response?.data?.detail || error.message))
  } finally {
    deletingCharId.value = null
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
