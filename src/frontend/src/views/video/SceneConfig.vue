<template>
  <div class="min-h-screen pt-24 pb-32 px-8 max-w-[1600px] mx-auto grid grid-cols-12 gap-8">
    <!-- Left: Character Selection -->
    <aside class="col-span-12 lg:col-span-3 flex flex-col gap-6">
      <div class="flex justify-between items-end">
        <h2 class="text-xl font-bold font-headline tracking-tight">角色选择</h2>
        <span class="text-xs text-on-surface-variant font-medium">已选 1/1</span>
      </div>
      <div class="bg-surface-container-low rounded-lg p-6 flex-1">
        <div class="grid grid-cols-2 gap-4">
          <div
            v-if="selectedCharacter"
            class="relative aspect-[3/4] rounded-lg overflow-hidden ring-2 ring-primary bg-surface-container-lowest cursor-pointer"
          >
            <img
              :src="selectedCharacter.selected_image"
              class="w-full h-full object-cover"
            />
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
            <div class="absolute bottom-3 left-3">
              <p class="text-white text-xs font-bold">{{ selectedCharacter.name }}</p>
            </div>
            <div class="absolute top-2 right-2 bg-primary text-white p-1 rounded-full">
              <span class="material-symbols-outlined text-[16px]">check</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Right: Scene Configuration -->
    <section class="col-span-12 lg:col-span-9 flex flex-col gap-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 flex-1">
        <!-- Prompting Section -->
        <div class="flex flex-col gap-6">
          <div class="flex flex-col gap-2">
            <h2 class="text-xl font-bold font-headline tracking-tight">场景动作描述</h2>
            <p class="text-sm text-on-surface-variant">精准的描述能帮助 AI 更好地理解您的创作意图</p>
          </div>
          <div class="relative bg-surface-container-lowest rounded-lg p-6 shadow-sm h-64 flex flex-col border border-primary/5">
            <textarea
              v-model="sceneDescription"
              class="w-full flex-1 bg-transparent border-none focus:ring-0 text-base resize-none"
              placeholder="描述当前场景或动作，例如：林克站在繁华的赛博朋克街头，雨水打湿了他的肩膀..."
            ></textarea>
            <div class="flex justify-between items-center pt-4 border-t border-surface-container">
              <span class="px-2 py-1 bg-surface-container text-[10px] rounded-full font-bold uppercase tracking-wider text-on-surface-variant">
                {{ sceneDescription.length }} / 500
              </span>
              <button class="flex items-center gap-2 bg-primary-container text-on-primary-container px-4 py-2 rounded-full text-xs font-bold hover:brightness-95 transition-all">
                <span class="material-symbols-outlined text-sm">auto_awesome</span>
                AI 智能扩写
              </button>
            </div>
          </div>
        </div>

        <!-- Parameters Section -->
        <div class="flex flex-col gap-6">
          <h2 class="text-xl font-bold font-headline tracking-tight">视频参数</h2>
          <div class="bg-surface-container-lowest rounded-lg p-8 shadow-sm border border-primary/5 flex flex-col gap-8">
            <!-- Model Selection -->
            <div class="flex flex-col gap-4">
              <label class="text-sm font-bold text-on-surface-variant flex items-center gap-2">
                <span class="material-symbols-outlined text-[18px]">neurology</span>
                模型选择
              </label>
              <div class="grid grid-cols-2 gap-3">
                <div
                  @click="selectedModel = 'cinematic'"
                  :class="[
                    'px-4 py-3 rounded-lg border-2 flex items-center justify-between cursor-pointer transition-colors',
                    selectedModel === 'cinematic'
                      ? 'border-primary bg-primary/5'
                      : 'border-outline-variant/30 hover:border-primary/50'
                  ]"
                >
                  <div class="flex flex-col">
                    <span :class="['text-sm font-bold', selectedModel === 'cinematic' ? 'text-primary' : '']">Cinematic v3</span>
                    <span class="text-[10px] text-on-surface-variant">极致影调 & 细节</span>
                  </div>
                  <span v-if="selectedModel === 'cinematic'" class="material-symbols-outlined text-primary text-xl">check_circle</span>
                </div>
                <div
                  @click="selectedModel = 'fast'"
                  :class="[
                    'px-4 py-3 rounded-lg border flex items-center justify-between cursor-pointer transition-colors',
                    selectedModel === 'fast'
                      ? 'border-primary bg-primary/5'
                      : 'border-outline-variant/30 hover:border-primary/50'
                  ]"
                >
                  <div class="flex flex-col">
                    <span class="text-sm font-bold">Fast Motion</span>
                    <span class="text-[10px] text-on-surface-variant">极速生成 & 稳定</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Duration & Aspect Ratio -->
            <div class="grid grid-cols-2 gap-8">
              <div class="flex flex-col gap-4">
                <label class="text-sm font-bold text-on-surface-variant">视频时长</label>
                <div class="flex items-center gap-2 bg-surface-container-low rounded-full px-4 py-2">
                  <span class="text-sm font-bold flex-1">{{ duration }}.0s</span>
                  <input v-model="duration" type="range" min="1" max="10" class="w-24 accent-primary" />
                </div>
              </div>
              <div class="flex flex-col gap-4">
                <label class="text-sm font-bold text-on-surface-variant">纵横比</label>
                <div class="flex gap-2">
                  <button
                    v-for="ratio in aspectRatios"
                    :key="ratio.value"
                    @click="aspectRatio = ratio.value"
                    :class="[
                      'flex-1 py-2 rounded-lg text-xs font-bold transition-colors',
                      aspectRatio === ratio.value
                        ? 'bg-primary text-white'
                        : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
                    ]"
                  >
                    {{ ratio.label }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Resolution -->
            <div class="flex flex-col gap-4">
              <label class="text-sm font-bold text-on-surface-variant">分辨率</label>
              <div class="flex gap-4">
                <label
                  v-for="res in resolutions"
                  :key="res.value"
                  class="flex-1 flex items-center gap-3 cursor-pointer group"
                >
                  <div
                    :class="[
                      'w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors',
                      resolution === res.value ? 'border-primary' : 'border-outline-variant group-hover:border-primary/50'
                    ]"
                  >
                    <div v-if="resolution === res.value" class="w-2.5 h-2.5 bg-primary rounded-full"></div>
                  </div>
                  <span :class="['text-sm font-medium', resolution === res.value ? '' : 'text-on-surface-variant']">
                    {{ res.label }}
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Bottom Action Bar -->
    <footer class="fixed bottom-8 w-full flex justify-center z-50">
      <div class="bg-white/80 backdrop-blur-2xl border border-on-surface-variant/10 rounded-full px-6 py-3 shadow-lg shadow-primary/10 flex justify-center gap-4">
        <router-link to="/video/select" class="text-on-surface-variant px-4 py-2 flex items-center gap-2 hover:bg-surface-container-low transition-colors rounded-full font-bold text-xs">
          <span class="material-symbols-outlined">arrow_back</span>
          上一步
        </router-link>
        <button
          @click="generateVideo"
          :disabled="!sceneDescription"
          class="bg-primary text-white rounded-full px-6 py-2 flex items-center gap-2 scale-105 active:scale-95 duration-300 font-bold text-xs shadow-lg shadow-primary/30 disabled:opacity-50"
        >
          <span class="material-symbols-outlined">arrow_forward</span>
          生成视频
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { videosApi } from '@/api/videos'

const router = useRouter()

const selectedCharacter = ref(null)
const sceneDescription = ref('')
const selectedModel = ref('cinematic')
const duration = ref(5)
const aspectRatio = ref('16:9')
const resolution = ref('1080p')

const aspectRatios = [
  { label: '16:9', value: '16:9' },
  { label: '9:16', value: '9:16' },
  { label: '1:1', value: '1:1' }
]

const resolutions = [
  { label: '720P', value: '720p' },
  { label: '1080P HD', value: '1080p' },
  { label: '4K Ultra', value: '4k' }
]

const generateVideo = async () => {
  try {
    const response = await videosApi.generate({
      character_id: selectedCharacter.value?.id,
      scene_description: sceneDescription.value,
      duration: duration.value,
      aspect_ratio: aspectRatio.value,
      resolution: resolution.value,
      model_provider: selectedModel.value
    })
    router.push('/video/result')
  } catch (error) {
    console.error('Failed to generate video:', error)
  }
}
</script>
