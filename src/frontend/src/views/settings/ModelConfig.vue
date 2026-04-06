<template>
  <div class="max-w-5xl mx-auto">
    <header class="mb-12">
      <h1 class="text-3xl font-extrabold tracking-tight font-headline text-on-background mb-2">模型配置</h1>
      <p class="text-on-surface-variant">配置您的 AI 引擎接口与生成参数，以获得最佳创作效果。</p>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <!-- Text Model -->
      <section class="bg-surface-container-lowest p-8 rounded-lg shadow-sm flex flex-col gap-6">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-primary/10 rounded-lg">
            <span class="material-symbols-outlined text-primary">description</span>
          </div>
          <h3 class="text-xl font-bold font-headline">文本 (Text)</h3>
        </div>
        <div class="space-y-4">
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型提供商</label>
            <select v-model="textModel.provider" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="qwen">通义千问 (阿里云百炼)</option>
              <option value="openai">GPT-4 Turbo</option>
              <option value="anthropic">Claude 3 Opus</option>
              <option value="deepseek">DeepSeek-V3</option>
            </select>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">API Key</label>
            <input
              v-model="textModel.api_key"
              type="password"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm"
              placeholder="sk-••••••••••••••••"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">参数微调 (Temperature)</label>
            <input v-model="textModel.temperature" type="range" min="0" max="2" step="0.1" class="w-full accent-primary" />
          </div>
        </div>
        <button
          @click="testConnection('text')"
          class="w-full mt-2 py-3 px-6 bg-surface-container-high text-primary font-bold rounded-full text-sm hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined text-[18px]">bolt</span>
          测试连接
        </button>
      </section>

      <!-- Image Model -->
      <section class="bg-surface-container-lowest p-8 rounded-lg shadow-sm flex flex-col gap-6 transform md:translate-y-6">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-tertiary/10 rounded-lg">
            <span class="material-symbols-outlined text-tertiary">image</span>
          </div>
          <h3 class="text-xl font-bold font-headline">图像 (Image)</h3>
        </div>
        <div class="space-y-4">
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型提供商</label>
            <select v-model="imageModel.provider" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="wanx">万相 (阿里云百炼)</option>
              <option value="qwen-image">千问图像 (阿里云百炼)</option>
              <option value="midjourney">Midjourney v6</option>
              <option value="stability">Stable Diffusion XL</option>
              <option value="dalle">DALL-E 3</option>
            </select>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">API Key</label>
            <input
              v-model="imageModel.api_key"
              type="password"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm"
              placeholder="••••••••••••••••"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">默认比例</label>
            <div class="flex gap-2">
              <button
                v-for="ratio in aspectRatios"
                :key="ratio"
                @click="imageModel.aspect_ratio = ratio"
                :class="[
                  'px-3 py-1 text-xs rounded-full transition-colors',
                  imageModel.aspect_ratio === ratio
                    ? 'bg-primary text-white'
                    : 'bg-surface-container-high text-on-surface-variant'
                ]"
              >
                {{ ratio }}
              </button>
            </div>
          </div>
        </div>
        <button
          @click="testConnection('image')"
          class="w-full mt-2 py-3 px-6 bg-surface-container-high text-primary font-bold rounded-full text-sm hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined text-[18px]">bolt</span>
          测试连接
        </button>
      </section>

      <!-- Video Model -->
      <section class="bg-surface-container-lowest p-8 rounded-lg shadow-sm flex flex-col gap-6">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-secondary/10 rounded-lg">
            <span class="material-symbols-outlined text-secondary">movie</span>
          </div>
          <h3 class="text-xl font-bold font-headline">视频 (Video)</h3>
        </div>
        <div class="space-y-4">
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型提供商</label>
            <select v-model="videoModel.provider" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="kling">可灵AI</option>
              <option value="runway">Runway Gen-2</option>
              <option value="pika">Pika Art</option>
            </select>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">API Key / Webhook URL</label>
            <input
              v-model="videoModel.api_key"
              type="text"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm"
              placeholder="https://api.yourdomain.com/callback"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">默认帧率 (FPS)</label>
            <select v-model="videoModel.fps" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="24">24 FPS</option>
              <option value="30">30 FPS</option>
              <option value="60">60 FPS</option>
            </select>
          </div>
        </div>
        <button
          @click="testConnection('video')"
          class="w-full mt-2 py-3 px-6 bg-surface-container-high text-primary font-bold rounded-full text-sm hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined text-[18px]">bolt</span>
          测试连接
        </button>
      </section>

      <!-- Voice Model -->
      <section class="bg-surface-container-lowest p-8 rounded-lg shadow-sm flex flex-col gap-6 transform md:translate-y-6">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-error/10 rounded-lg">
            <span class="material-symbols-outlined text-error">record_voice_over</span>
          </div>
          <h3 class="text-xl font-bold font-headline">语音 (Voice)</h3>
        </div>
        <div class="space-y-4">
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型提供商</label>
            <select v-model="voiceModel.provider" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="cosyvoice">CosyVoice (阿里云百炼)</option>
              <option value="elevenlabs">ElevenLabs</option>
              <option value="azure">Azure Speech</option>
              <option value="openai">OpenAI TTS</option>
            </select>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">API Key / Voice ID</label>
            <input
              v-model="voiceModel.api_key"
              type="text"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm"
              placeholder="EX: pNInz6ob8mwvPs_1"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">参数微调 (Stability)</label>
            <input v-model="voiceModel.stability" type="range" min="0" max="1" step="0.1" class="w-full accent-error" />
          </div>
        </div>
        <button
          @click="testConnection('voice')"
          class="w-full mt-2 py-3 px-6 bg-surface-container-high text-primary font-bold rounded-full text-sm hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined text-[18px]">bolt</span>
          测试连接
        </button>
      </section>
    </div>

    <!-- Save Button -->
    <div class="mt-8 flex justify-end">
      <button
        @click="saveConfig"
        class="px-8 py-3 bg-primary text-white font-bold rounded-full text-sm hover:bg-primary-dim transition-colors"
      >
        保存配置
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { modelConfigApi } from '@/api/modelConfig'

const aspectRatios = ['16:9', '9:16', '1:1']

const textModel = ref({
  provider: 'openai',
  api_key: '',
  temperature: 0.7
})

const imageModel = ref({
  provider: 'midjourney',
  api_key: '',
  aspect_ratio: '16:9'
})

const videoModel = ref({
  provider: 'kling',
  api_key: '',
  fps: '24'
})

const voiceModel = ref({
  provider: 'elevenlabs',
  api_key: '',
  stability: 0.5
})

const testConnection = async (type) => {
  try {
    const model = { text: textModel, image: imageModel, video: videoModel, voice: voiceModel }[type]
    const response = await modelConfigApi.test({
      provider: model.value.provider,
      api_key: model.value.api_key
    })
    if (response.data.success) {
      alert('连接成功！')
    } else {
      alert('连接失败：' + response.data.message)
    }
  } catch (error) {
    alert('连接测试失败')
  }
}

const saveConfig = async () => {
  try {
    await Promise.all([
      modelConfigApi.updateOrCreate({ name: 'text', ...textModel.value }),
      modelConfigApi.updateOrCreate({ name: 'image', ...imageModel.value }),
      modelConfigApi.updateOrCreate({ name: 'video', ...videoModel.value }),
      modelConfigApi.updateOrCreate({ name: 'voice', ...voiceModel.value })
    ])
    alert('配置已保存')
  } catch (error) {
    alert('保存失败，请重试')
  }
}

onMounted(async () => {
  try {
    const response = await modelConfigApi.getAll()
    response.data.forEach(config => {
      if (config.name === 'text') {
        textModel.value = { ...textModel.value, ...config }
      } else if (config.name === 'image') {
        imageModel.value = { ...imageModel.value, ...config }
      } else if (config.name === 'video') {
        videoModel.value = { ...videoModel.value, ...config }
      } else if (config.name === 'voice') {
        voiceModel.value = { ...voiceModel.value, ...config }
      }
    })
  } catch (error) {
    console.error('Failed to load config:', error)
  }
})
</script>
