<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-8">
    <div class="bg-surface-container-lowest rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="p-6 border-b border-surface-container flex justify-between items-center">
        <h2 class="text-xl font-bold font-headline">
          为"{{ character?.name }}"生成角色形象
        </h2>
        <button @click="$emit('close')" class="p-2 hover:bg-surface-container rounded-full transition-colors">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 flex-1 overflow-y-auto">
        <!-- Character Description -->
        <div class="mb-6">
          <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2 block">角色描述</label>
          <p class="text-sm text-on-surface bg-surface-container-low p-4 rounded-lg">
            {{ character?.appearance || '暂无描述' }}
          </p>
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

        <!-- Prompt Override -->
        <div class="mb-6">
          <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2 block">补充提示词</label>
          <textarea
            v-model="promptSuffix"
            rows="3"
            class="w-full bg-surface-container-low border-none rounded-lg text-sm p-4"
            placeholder="输入你的补充内容，会追加到默认模板后面..."
          ></textarea>
        </div>

        <!-- Error Display -->
        <div v-if="generationError" class="mb-4 bg-red-50 text-red-700 rounded-lg p-3 text-sm">
          {{ generationError }}
        </div>

        <!-- Loading State -->
        <div v-if="generating || generatingThreeViews" class="mb-6 text-center py-8">
          <span class="material-symbols-outlined text-3xl text-primary animate-spin mb-2">autorenew</span>
          <p class="text-sm text-on-surface-variant">{{ generating ? '正在生成形象...' : '正在生成三视图...' }}</p>
        </div>

        <!-- Generated Images -->
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

        <!-- Three Views -->
        <div v-if="threeViews" class="mb-6">
          <div class="flex items-center justify-between mb-3">
            <label class="text-xs font-bold uppercase tracking-wider text-on-surface-variant block">三视图</label>
            <span class="text-xs text-on-surface-variant">(正面/侧面/背面)</span>
          </div>
          <div class="flex gap-2 mb-4">
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
          <div class="aspect-[3/4] bg-surface-container-low rounded-lg overflow-hidden">
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
            <p v-if="selectedStyles.length === 0" class="text-xs text-red-500 mt-1">请至少选择一种风格</p>
          </div>
          <button
            @click="generateThreeViews"
            :disabled="generating"
            class="px-6 py-3 bg-surface-container-high text-primary font-bold rounded-full text-sm hover:bg-primary hover:text-white transition-all disabled:opacity-50"
          >
            {{ generatingThreeViews ? '三视图生成中...' : '生成三视图' }}
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
import { ref } from 'vue'
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

const selectedStyles = ref(['realistic'])
const promptSuffix = ref('')
const generatedImages = ref(null)
const selectedImage = ref(null)
const generating = ref(false)
const generatingThreeViews = ref(false)
const generationError = ref('')
const threeViews = ref(null)
const activeView = ref('front')

const viewTypes = [
  { key: 'front', label: '正面' },
  { key: 'side', label: '侧面' },
  { key: 'back', label: '背面' }
]

const toggleStyle = (styleId) => {
  const index = selectedStyles.value.indexOf(styleId)
  if (index > -1) {
    selectedStyles.value.splice(index, 1)
  } else {
    selectedStyles.value.push(styleId)
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
      style: selectedStyles.value[0] || 'realistic',
      prompt_suffix: promptSuffix.value
    })
    threeViews.value = response.data
    // Only auto-select if no image is selected yet
    if (response.data.views?.front && !selectedImage.value) {
      selectedImage.value = response.data.views.front
    }
  } catch (error) {
    generationError.value = '三视图生成失败：' + (error.response?.data?.detail || error.message)
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
