<template>
  <div class="min-h-screen pt-24 pb-32 px-8 max-w-7xl mx-auto">
    <div class="mb-12">
      <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">
        新建短剧项目
      </h1>
      <p class="text-on-surface-variant">
        开启您的 AI 驱动创意旅程，一键生成高质量短剧剧本与视频。
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Main Form -->
      <div class="lg:col-span-8 space-y-8">
        <!-- Basic Info -->
        <div class="bg-surface-container-lowest p-8 rounded-lg shadow-sm">
          <div class="space-y-6">
            <div class="space-y-2">
              <label class="text-sm font-semibold text-on-surface flex items-center gap-2">
                <span class="material-symbols-outlined text-sm">edit_note</span>
                项目名称
              </label>
              <input
                v-model="form.name"
                type="text"
                class="w-full bg-surface-container-low border-none rounded-lg focus:ring-2 focus:ring-primary/20 p-4"
                placeholder="输入您的项目名称，如：AI之城的秘密"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-semibold text-on-surface flex items-center gap-2">
                <span class="material-symbols-outlined text-sm">description</span>
                创作描述
              </label>
              <textarea
                v-model="form.description"
                rows="6"
                class="w-full bg-surface-container-low border-none rounded-lg focus:ring-2 focus:ring-primary/20 p-4 resize-none"
                placeholder="描述您想要创作的故事情节、核心冲突或主要场景... AI 将根据您的描述自动扩展剧情。"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Parameters -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-surface-container-low p-6 rounded-lg space-y-4">
            <label class="text-sm font-bold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-xl">theater_comedy</span>
              类型
            </label>
            <select v-model="form.genre" class="w-full bg-surface-container-lowest border-none rounded-full px-4 py-2 text-sm">
              <option>都市言情</option>
              <option>悬疑惊悚</option>
              <option>古代宫廷</option>
              <option>科幻未来</option>
              <option>职场励志</option>
            </select>
          </div>

          <div class="bg-surface-container-low p-6 rounded-lg space-y-4">
            <label class="text-sm font-bold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-xl">palette</span>
              风格
            </label>
            <select v-model="form.style" class="w-full bg-surface-container-lowest border-none rounded-full px-4 py-2 text-sm">
              <option>电影质感</option>
              <option>动漫渲染</option>
              <option>复古胶片</option>
              <option>极简主义</option>
              <option>赛博朋克</option>
            </select>
          </div>

          <div class="bg-surface-container-low p-6 rounded-lg space-y-4">
            <label class="text-sm font-bold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-xl">ios_share</span>
              目标平台
            </label>
            <select v-model="form.target_platform" class="w-full bg-surface-container-lowest border-none rounded-full px-4 py-2 text-sm">
              <option>抖音 (9:16)</option>
              <option>快手 (9:16)</option>
              <option>Bilibili (16:9)</option>
              <option>YouTube Shorts</option>
            </select>
          </div>

          <div class="bg-surface-container-low p-6 rounded-lg space-y-4">
            <label class="text-sm font-bold text-on-surface flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-xl">view_list</span>
              集数规模
            </label>
            <select v-model="form.episode_tier" class="w-full bg-surface-container-lowest border-none rounded-full px-4 py-2 text-sm">
              <option value="short">短篇 (8-20集)</option>
              <option value="medium">中篇 (20-50集)</option>
              <option value="long">长篇 (80-120集)</option>
            </select>
          </div>
        </div>

        <!-- Advanced Options -->
        <div class="bg-surface-container-low rounded-lg overflow-hidden">
          <button
            @click="showAdvanced = !showAdvanced"
            class="w-full p-6 flex justify-between items-center text-on-surface hover:bg-surface-container-high transition-colors"
          >
            <span class="flex items-center gap-3 font-semibold">
              <span class="material-symbols-outlined text-primary">tune</span>
              高级配置选项
            </span>
            <span class="material-symbols-outlined transition-transform" :class="{ 'rotate-180': showAdvanced }">
              expand_more
            </span>
          </button>
          <div v-if="showAdvanced" class="p-8 pt-0 space-y-6">
            <div class="space-y-3">
              <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant">自定义 Prompt</label>
              <textarea
                v-model="form.prompt_suffix"
                rows="3"
                class="w-full bg-surface-container-lowest border-none rounded-lg text-sm p-4"
                placeholder="输入特定的AI指令，精细化控制生成方向..."
              ></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- Preview Card -->
      <div class="lg:col-span-4">
        <div class="bg-primary p-8 rounded-lg text-on-primary sticky top-24 shadow-lg shadow-primary/20">
          <h3 class="font-headline font-bold text-xl mb-6">项目预览摘要</h3>
          <ul class="space-y-4 mb-8">
            <li class="flex justify-between items-center pb-4 border-b border-on-primary/10">
              <span class="opacity-70 text-sm">时长预估</span>
              <span class="font-bold">约 {{ form.duration }}s</span>
            </li>
            <li class="flex justify-between items-center pb-4 border-b border-on-primary/10">
              <span class="opacity-70 text-sm">题材类型</span>
              <span class="font-bold">{{ form.genre || '未设置' }}</span>
            </li>
            <li class="flex justify-between items-center">
              <span class="opacity-70 text-sm">目标平台</span>
              <span class="font-bold">{{ form.target_platform || '未设置' }}</span>
            </li>
          </ul>
          <button
            @click="createProject"
            :disabled="loading || !form.name"
            class="w-full bg-white text-primary font-bold py-4 rounded-full flex items-center justify-center gap-2 hover:bg-on-primary transition-all active:scale-95 disabled:opacity-50"
          >
            {{ loading ? '创建中...' : '创建项目' }}
            <span class="material-symbols-outlined">rocket_launch</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'

const router = useRouter()
const loading = ref(false)
const showAdvanced = ref(false)

const form = reactive({
  name: '',
  description: '',
  genre: '都市言情',
  style: '电影质感',
  target_platform: '抖音 (9:16)',
  duration: 180,
  prompt_suffix: '',
  type: 'drama'
})

const createProject = async () => {
  if (!form.name) return

  loading.value = true
  try {
    const response = await projectsApi.create(form)
    router.push(`/drama/${response.data.id}`)
  } catch (error) {
    console.error('Failed to create project:', error)
    alert('创建项目失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>
