<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-8">
    <div class="bg-surface-container-lowest rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="p-6 border-b border-surface-container flex justify-between items-center">
        <h2 class="text-xl font-bold font-headline">
          为"{{ character?.name }}"生成角色设计图
        </h2>
        <button @click="$emit('close')" class="p-2 hover:bg-surface-container rounded-full transition-colors">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 flex-1 overflow-y-auto">
        <!-- Character Info -->
        <div class="mb-6">
          <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2 block">角色信息</label>
          <div class="bg-surface-container-low p-4 rounded-lg">
            <div class="flex items-start gap-4">
              <!-- Existing image preview -->
              <div v-if="character?.selected_image" class="w-24 h-32 rounded-lg overflow-hidden flex-shrink-0 bg-surface-container">
                <img :src="toPlayableUrl(character.selected_image)" class="w-full h-full object-cover" />
              </div>
              <div v-else class="w-24 h-32 rounded-lg flex-shrink-0 bg-surface-container flex items-center justify-center">
                <span class="material-symbols-outlined text-3xl text-on-surface-variant/50">person</span>
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <span v-if="character?.age" class="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">{{ character.age }}岁</span>
                  <span v-if="character?.gender" class="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">{{ character.gender }}</span>
                  <span v-if="character?.occupation" class="text-xs bg-surface-container text-on-surface-variant px-2 py-0.5 rounded-full">{{ character.occupation }}</span>
                </div>
                <p v-if="character?.personality" class="text-xs text-on-surface-variant mb-2">
                  <strong>性格:</strong> {{ character.personality }}
                </p>
                <p v-if="character?.appearance" class="text-xs text-on-surface mb-1">
                  <strong>外貌:</strong> {{ character.appearance }}
                </p>
                <p v-if="character?.clothing" class="text-xs text-on-surface-variant">
                  <strong>服装:</strong> {{ character.clothing }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Existing Design Sheet -->
        <div v-if="character?.three_views?.design_sheet || character?.selected_image" class="mb-6">
          <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2 block">当前形象</label>
          <div class="bg-surface-container-low rounded-lg overflow-hidden max-w-md">
            <img
              :src="toPlayableUrl(character.three_views?.design_sheet || character.selected_image)"
              class="w-full object-contain"
            />
          </div>
        </div>

        <!-- Style Selection -->
        <div class="mb-6">
          <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-3 block">生成风格</label>
          <div class="flex gap-2 flex-wrap">
            <button
              v-for="style in styles"
              :key="style.id"
              @click="toggleStyle(style.id)"
              :class="[
                'px-4 py-2 rounded-full text-sm font-medium transition-colors',
                selectedStyles.includes(style.id)
                  ? 'bg-primary text-white'
                  : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
              ]"
            >
              {{ style.name }}
            </button>
          </div>
        </div>

        <!-- Prompt Preview & Edit -->
        <div class="mb-6">
          <div class="flex items-center justify-between mb-2">
            <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant">提示词预览 & 编辑</label>
            <button
              @click="fetchPromptPreview"
              :disabled="loadingPrompt"
              class="text-xs font-bold text-primary flex items-center gap-1 hover:underline"
            >
              <span class="material-symbols-outlined text-sm">refresh</span>
              {{ loadingPrompt ? '加载中...' : '刷新提示词' }}
            </button>
          </div>
          <textarea
            v-model="customPrompt"
            rows="6"
            class="w-full bg-surface-container-low border border-surface-container rounded-lg text-sm p-4 font-mono resize-y"
            placeholder="点击'刷新提示词'获取自动生成的提示词，或直接输入自定义提示词..."
          ></textarea>
          <p class="text-xs text-on-surface-variant mt-1">
            左侧为三视图（正面/侧面/背面）+ 右侧为4种表情（开心/愤怒/惊讶/悲伤），排列在一张角色设计表上
          </p>
        </div>

        <!-- Error Display -->
        <div v-if="generationError" class="mb-4 bg-red-50 text-red-700 rounded-lg p-3 text-sm whitespace-pre-wrap">
          {{ generationError }}
        </div>

        <!-- Loading -->
        <div v-if="generating || generatingThreeViews" class="mb-6 text-center py-8">
          <span class="material-symbols-outlined text-3xl text-primary animate-spin mb-2">autorenew</span>
          <p class="text-sm text-on-surface-variant">{{ generating ? '正在生成形象...' : '正在生成角色设计图（三视图+表情）...' }}</p>
        </div>

        <!-- Generated Images (old style: separate images per style) -->
        <div v-if="generatedImages && Object.keys(generatedImages).length > 0">
          <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-3 block">生成结果</label>
          <div v-for="(images, style) in generatedImages" :key="style" class="mb-6">
            <h4 class="text-sm font-bold mb-3">{{ style }}</h4>
            <div class="grid grid-cols-4 gap-3">
              <div
                v-for="(img, index) in images"
                :key="index"
                @click="selectedImage = img"
                :class="[
                  'aspect-square rounded-lg overflow-hidden cursor-pointer border-2 transition-all',
                  selectedImage === img ? 'border-primary ring-2 ring-primary/20' : 'border-transparent hover:border-outline-variant'
                ]"
              >
                <img :src="img" class="w-full h-full object-cover" />
              </div>
            </div>
          </div>
        </div>

        <!-- Combined Design Sheet (new: three-views + expressions on one image) -->
        <div v-if="threeViews" class="mb-6">
          <div class="flex items-center justify-between mb-3">
            <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant block">角色设计图（三视图 + 表情）</label>
            <span v-if="threeViews.views?.expressions" class="text-xs text-on-surface-variant">
              表情: {{ threeViews.views.expressions.join(', ') }}
            </span>
          </div>
          <!-- Combined design sheet -->
          <div class="aspect-[16/10] bg-surface-container-low rounded-lg overflow-hidden max-w-2xl">
            <img
              v-if="threeViews.views?.design_sheet"
              :src="threeViews.views.design_sheet"
              class="w-full h-full object-contain"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-on-surface-variant text-sm">
              设计图加载中...
            </div>
          </div>
          <!-- Fallback: individual views (old format) -->
          <div v-if="!threeViews.views?.combined && threeViews.views?.front" class="mt-4">
            <p class="text-xs text-on-surface-variant mb-2">旧格式三视图（分别显示）</p>
            <div class="flex gap-2">
              <button
                v-for="vt in viewTypes"
                :key="vt.key"
                @click="activeView = vt.key"
                :class="[
                  'px-4 py-2 rounded-full text-xs font-bold transition-colors',
                  activeView === vt.key
                    ? 'bg-primary text-white'
                    : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
                ]"
              >
                {{ vt.label }}
              </button>
            </div>
            <div class="aspect-[3/4] bg-surface-container-low rounded-lg overflow-hidden mt-2 max-w-xs">
              <img
                v-if="threeViews.views?.[activeView]"
                :src="threeViews.views[activeView]"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-on-surface-variant text-sm">
                暂无 {{ activeView === 'front' ? '正面' : activeView === 'side' ? '侧面' : '背面' }} 视图
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-surface-container flex justify-between">
        <div class="flex gap-3">
          <div>
            <button
              @click="generateImages"
              :disabled="generating || selectedStyles.length === 0"
              class="px-6 py-3 bg-surface-container-high text-primary font-bold rounded-full text-sm hover:bg-primary hover:text-white transition-all disabled:opacity-50"
            >
              {{ generating ? '生成中...' : '生成形象' }}
            </button>
          </div>
          <button
            @click="generateThreeViews"
            :disabled="generatingThreeViews"
            class="px-6 py-3 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-all disabled:opacity-50 flex items-center gap-2"
          >
            <span class="material-symbols-outlined text-sm">auto_awesome</span>
            {{ generatingThreeViews ? '生成中...' : '生成设计图（三视图+表情）' }}
          </button>
        </div>
        <div class="flex gap-3">
          <button
            @click="$emit('close')"
            class="px-6 py-3 bg-surface-container text-on-surface-variant font-bold rounded-full text-sm hover:bg-surface-container-high transition-colors"
          >
            取消
          </button>
          <button
            @click="confirmSelection"
            :disabled="!selectedImage"
            class="px-6 py-3 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors disabled:opacity-50"
          >
            确认选择
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { charactersApi } from '@/api/characters'

const props = defineProps({
  character: Object
})

const emit = defineEmits(['close', 'select'])

const styles = [
  { id: 'realistic', name: '写实风' },
  { id: 'anime', name: '动漫风' },
  { id: 'cinematic', name: '电影质感' },
  { id: 'watercolor', name: '水墨风' }
]

const selectedStyles = ref(['anime'])
const promptSuffix = ref('')
const customPrompt = ref('')
const generatedImages = ref(null)
const selectedImage = ref(null)
const generating = ref(false)
const generatingThreeViews = ref(false)
const generationError = ref('')
const threeViews = ref(null)
const activeView = ref('front')
const loadingPrompt = ref(false)

const viewTypes = [
  { key: 'front', label: '正面' },
  { key: 'side', label: '侧面' },
  { key: 'back', label: '背面' }
]

function toPlayableUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const idx = url.indexOf('/media/')
  if (idx !== -1) return url.substring(idx)
  return url
}

// Load prompt preview when character changes
watch(() => props.character, (newChar) => {
  if (newChar) {
    fetchPromptPreview()
  }
}, { immediate: true })

const toggleStyle = (styleId) => {
  const index = selectedStyles.value.indexOf(styleId)
  if (index > -1) {
    selectedStyles.value.splice(index, 1)
  } else {
    selectedStyles.value.push(styleId)
  }
}

const fetchPromptPreview = async () => {
  if (!props.character?.id) return
  loadingPrompt.value = true
  try {
    const res = await charactersApi.previewThreeViewsPrompt(
      props.character.id,
      { style: selectedStyles.value[0] || 'anime', prompt_suffix: promptSuffix.value }
    )
    if (res.data?.prompt) {
      customPrompt.value = res.data.prompt
    }
  } catch (error) {
    console.error('Failed to fetch prompt preview:', error)
  } finally {
    loadingPrompt.value = false
  }
}

const generateImages = async () => {
  generating.value = true
  generationError.value = ''
  try {
    const response = await charactersApi.generateImage(props.character.id, {
      styles: selectedStyles.value,
      count_per_style: 4,
      prompt_suffix: promptSuffix.value
    })
    generatedImages.value = response.data.images
  } catch (error) {
    generationError.value = '形象生成失败：' + (error.response?.data?.detail || error.message)
  } finally {
    generating.value = false
  }
}

const generateThreeViews = async () => {
  generatingThreeViews.value = true
  generationError.value = ''
  try {
    const response = await charactersApi.generateThreeViews(props.character.id, {
      style: selectedStyles.value[0] || 'anime',
      prompt_suffix: promptSuffix.value,
      custom_prompt: customPrompt.value || ''
    })
    threeViews.value = response.data
    if (response.data.views?.design_sheet && !selectedImage.value) {
      selectedImage.value = response.data.views.design_sheet
    } else if (response.data.views?.front && !selectedImage.value) {
      selectedImage.value = response.data.views.front
    }
  } catch (error) {
    generationError.value = '设计图生成失败：' + (error.response?.data?.detail || error.message)
  } finally {
    generatingThreeViews.value = false
  }
}

const confirmSelection = () => {
  if (selectedImage.value) {
    emit('select', {
      characterId: props.character.id,
      imageUrl: selectedImage.value
    })
    emit('close')
  }
}
</script>
