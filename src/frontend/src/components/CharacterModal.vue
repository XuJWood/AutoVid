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
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-surface-container flex justify-between">
        <button
          @click="generateImages"
          :disabled="generating || selectedStyles.length === 0"
          class="px-6 py-3 bg-surface-container-high text-primary font-bold rounded-full text-sm hover:bg-primary hover:text-white transition-all disabled:opacity-50"
        >
          {{ generating ? '生成中...' : '生成形象' }}
        </button>
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
import { ref, defineProps, defineEmits } from 'vue'
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
  try {
    const response = await charactersApi.generateImage(props.character.id, {
      styles: selectedStyles.value,
      count_per_style: 4,
      prompt_suffix: promptSuffix.value
    })
    generatedImages.value = response.data.images
  } catch (error) {
    console.error('Failed to generate images:', error)
  } finally {
    generating.value = false
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
