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
          <span class="text-xs text-on-surface-variant ml-auto">用于剧本生成</span>
        </div>
        <div class="space-y-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型提供商</label>
            <select v-model="textModel.provider" @change="onTextProviderChange" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="qwen">通义千问 (阿里云百炼)</option>
              <option value="deepseek-anthropic">DeepSeek-V4-Pro (Anthropic接口/推荐)</option>
              <option value="deepseek">DeepSeek (OpenAI接口)</option>
              <option value="openai">OpenAI GPT</option>
              <option value="anthropic">Anthropic Claude</option>
            </select>
            <p class="text-[11px] text-on-surface-variant/70" v-if="textModel.provider === 'deepseek-anthropic'">
              DeepSeek 提供的 Anthropic 兼容接口，支持 deepseek-v4-pro 等模型
            </p>
            <p class="text-[11px] text-on-surface-variant/70" v-else-if="textModel.provider === 'qwen'">
              阿里云百炼，国内访问稳定，价格便宜
            </p>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型</label>
            <input
              v-model="textModel.model"
              type="text"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm font-mono"
              :placeholder="textModelPlaceholder"
            />
            <p class="text-[11px] text-on-surface-variant/70">
              常见: qwen-plus / deepseek-v4-pro / claude-sonnet-4-5-20250929 / gpt-4-turbo
            </p>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">API Key</label>
            <input
              v-model="textModel.api_key"
              type="password"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm font-mono"
              placeholder="sk-•••••••••••••••• / sk-ant-•••"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Base URL（可选）</label>
            <input
              v-model="textModel.base_url"
              type="text"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm font-mono"
              :placeholder="textBaseUrlPlaceholder"
            />
            <p class="text-[11px] text-on-surface-variant/70">
              留空使用提供商默认地址。<span v-if="textModel.provider === 'deepseek-anthropic'">DeepSeek Anthropic 接口默认: <code class="bg-surface-container-high px-1 rounded">https://api.deepseek.com/anthropic</code></span>
            </p>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
              Temperature: {{ Number(textModel.temperature).toFixed(1) }}
            </label>
            <input v-model="textModel.temperature" type="range" min="0" max="2" step="0.1" class="w-full accent-primary" />
            <p class="text-[11px] text-on-surface-variant/70">越高越有创意，越低越严谨。剧本生成推荐 0.7-0.9</p>
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
            <select v-model="imageModel.provider" @change="onImageProviderChange" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="seedream">Seedream 4.5 (火山引擎/推荐)</option>
              <option value="wanx">万相 (阿里云百炼)</option>
              <option value="qwen-image">千问图像 (阿里云百炼)</option>
              <option value="midjourney">Midjourney v6</option>
              <option value="stability">Stable Diffusion XL</option>
              <option value="dalle">DALL-E 3</option>
            </select>
            <p class="text-[11px] text-on-surface-variant/70" v-if="imageModel.provider === 'seedream'">
              火山引擎 Ark 平台，Seedream 4.5 模型，支持 2K/4K 分辨率
            </p>
            <p class="text-[11px] text-on-surface-variant/70" v-else-if="imageModel.provider === 'wanx'">
              阿里云百炼平台，使用 DashScope API Key
            </p>
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型</label>
            <select v-model="imageModel.model" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <template v-if="imageModel.provider === 'seedream'">
                <option value="doubao-seedream-4-5-251128">Seedream 4.5 (推荐)</option>
                <option value="doubao-seedream-4-0-251128">Seedream 4.0</option>
              </template>
              <template v-else>
                <option value="wanx2.1-t2i-turbo">wanx2.1-t2i-turbo</option>
                <option value="wanx2.1-t2i-plus">wanx2.1-t2i-plus</option>
              </template>
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
          <div class="flex flex-col gap-2" v-if="imageModel.provider === 'seedream'">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">API 地址</label>
            <input
              v-model="imageModel.base_url"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm"
              placeholder="https://ark.cn-beijing.volces.com/api/v3"
            />
            <p class="text-[11px] text-on-surface-variant/70">留空使用默认地址</p>
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
      <section class="bg-surface-container-lowest p-8 rounded-lg shadow-sm flex flex-col gap-6 md:col-span-2">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-secondary/10 rounded-lg">
            <span class="material-symbols-outlined text-secondary">movie</span>
          </div>
          <h3 class="text-xl font-bold font-headline">视频 (Video)</h3>
          <span class="text-xs text-on-surface-variant ml-auto">支持 Seedance 2.0 视频+音频一体化生成</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Provider -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">模型提供商</label>
            <select v-model="videoModel.provider" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="seedance">Seedance 2.0 (火山引擎/推荐)</option>
              <option value="wanx">万相 (阿里云百炼)</option>
              <option value="kling">可灵AI</option>
              <option value="runway">Runway Gen-2</option>
              <option value="pika">Pika Art</option>
            </select>
            <p class="text-[11px] text-on-surface-variant/70">推荐 Seedance — 视频自带音频对白，无需单独 TTS</p>
          </div>

          <!-- Model -->
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">具体模型</label>
            <select v-model="videoModel.model" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
              <option value="doubao-seedance-2-0-fast-260128">Seedance 2.0 Fast (便宜/推荐测试)</option>
              <option value="doubao-seedance-2-0-260128">Seedance 2.0 标准版 (质量最高)</option>
              <option value="doubao-seedance-1-5-pro-251215">Seedance 1.5 Pro</option>
              <option value="wan2.7-i2v">wan2.7-i2v (万相 图生视频)</option>
              <option value="wan2.7-t2v">wan2.7-t2v (万相 文生视频)</option>
              <option value="wanx2.1-t2v-turbo">wanx2.1-t2v-turbo (万相 旧版)</option>
            </select>
            <p class="text-[11px] text-on-surface-variant/70">Fast 比标准版便宜 30-50%，质量略低，适合开发调试</p>
          </div>

          <!-- API Key -->
          <div class="flex flex-col gap-1.5 md:col-span-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">API Key</label>
            <input
              v-model="videoModel.api_key"
              type="password"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm font-mono"
              placeholder="ark-•••••••••••••••• (火山引擎)  或  sk-•••••••••••••••• (DashScope)"
            />
            <p class="text-[11px] text-on-surface-variant/70">
              火山引擎: 在 <a href="https://console.volcengine.com/ark/region:ark+cn-beijing/apikey" target="_blank" class="text-primary underline">Ark 控制台</a> 创建 (前缀 ark-)；DashScope: 阿里云百炼控制台 (前缀 sk-)
            </p>
          </div>

          <!-- Base URL (advanced) -->
          <div class="flex flex-col gap-1.5 md:col-span-2">
            <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Base URL（可选）</label>
            <input
              v-model="videoModel.base_url"
              type="text"
              class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm font-mono"
              placeholder="留空使用默认: https://ark.cn-beijing.volces.com/api/v3"
            />
            <p class="text-[11px] text-on-surface-variant/70">仅在使用代理或自托管 API 时需要，普通用户留空即可</p>
          </div>
        </div>

        <!-- Generation Parameters -->
        <div class="border-t border-surface-container pt-4">
          <h4 class="text-sm font-bold mb-3 flex items-center gap-2">
            <span class="material-symbols-outlined text-base text-primary">tune</span>
            视频生成参数（默认值，每次生成可单独覆盖）
          </h4>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Duration -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant flex items-center gap-1">
                视频时长（秒）
                <span class="text-on-surface-variant/50" title="决定生成视频的长度">ⓘ</span>
              </label>
              <select v-model.number="videoParams.duration" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
                <option :value="4">4s (最短/最便宜)</option>
                <option :value="5">5s</option>
                <option :value="8">8s</option>
                <option :value="10">10s</option>
                <option :value="12">12s</option>
                <option :value="15">15s (推荐/匹配片段时长)</option>
              </select>
              <p class="text-[11px] text-on-surface-variant/70">越长越贵。Seedance 2.0 支持 4-15 秒。1080p×15s ≈ ¥6.5</p>
            </div>

            <!-- Resolution -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">分辨率</label>
              <select v-model="videoParams.resolution" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
                <option value="480p">480p (省流/快速预览)</option>
                <option value="720p">720p (HD)</option>
                <option value="1080p">1080p (Full HD/推荐)</option>
              </select>
              <p class="text-[11px] text-on-surface-variant/70">分辨率影响画面清晰度和价格。1080p 比 720p 贵约 2-3 倍</p>
            </div>

            <!-- Aspect Ratio -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">画面比例</label>
              <select v-model="videoParams.ratio" class="w-full bg-surface-container-low border-none rounded-lg p-3 text-sm">
                <option value="16:9">16:9 (横屏/B站/YouTube)</option>
                <option value="9:16">9:16 (竖屏/抖音/快手)</option>
                <option value="1:1">1:1 (方形/Instagram)</option>
                <option value="4:3">4:3</option>
                <option value="3:4">3:4</option>
                <option value="21:9">21:9 (电影宽屏)</option>
              </select>
              <p class="text-[11px] text-on-surface-variant/70">短剧抖音平台用 9:16 竖屏，B站长视频用 16:9</p>
            </div>

            <!-- Generate Audio Toggle -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">嵌入音频</label>
              <div class="flex items-center gap-3 bg-surface-container-low rounded-lg p-3">
                <input
                  v-model="videoParams.generate_audio"
                  type="checkbox"
                  id="gen-audio"
                  class="w-4 h-4 accent-primary"
                />
                <label for="gen-audio" class="text-sm cursor-pointer">生成视频时自动合成对白音频</label>
              </div>
              <p class="text-[11px] text-on-surface-variant/70">开启后视频自带角色配音；关闭则只有画面（仅 Seedance 2.0 支持）</p>
            </div>

            <!-- Watermark Toggle -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">添加水印</label>
              <div class="flex items-center gap-3 bg-surface-container-low rounded-lg p-3">
                <input
                  v-model="videoParams.watermark"
                  type="checkbox"
                  id="watermark"
                  class="w-4 h-4 accent-primary"
                />
                <label for="watermark" class="text-sm cursor-pointer">在视频右下角添加平台水印</label>
              </div>
              <p class="text-[11px] text-on-surface-variant/70">开发测试建议关闭；商用时需关注平台合规要求</p>
            </div>

            <!-- Cost Estimate -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">预估单价</label>
              <div class="bg-primary/10 rounded-lg p-3 text-sm">
                <div class="font-bold text-primary">{{ estimatedPrice }}</div>
                <div class="text-[11px] text-on-surface-variant mt-0.5">{{ priceFormula }}</div>
              </div>
            </div>
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
import { ref, computed, onMounted } from 'vue'
import { modelConfigApi } from '@/api/modelConfig'

const aspectRatios = ['16:9', '9:16', '1:1']

const textModel = ref({
  provider: 'qwen',
  model: 'qwen-plus',
  api_key: '',
  base_url: '',
  temperature: 0.7
})

const TEXT_PROVIDER_DEFAULTS = {
  'qwen': { model: 'qwen-plus', base_url: '' },
  'deepseek-anthropic': { model: 'deepseek-v4-pro', base_url: 'https://api.deepseek.com/anthropic' },
  'deepseek': { model: 'deepseek-chat', base_url: 'https://api.deepseek.com/v1' },
  'openai': { model: 'gpt-4-turbo', base_url: '' },
  'anthropic': { model: 'claude-sonnet-4-5-20250929', base_url: '' },
}

const textModelPlaceholder = computed(() => {
  return TEXT_PROVIDER_DEFAULTS[textModel.value.provider]?.model || 'model name'
})

const textBaseUrlPlaceholder = computed(() => {
  const def = TEXT_PROVIDER_DEFAULTS[textModel.value.provider]?.base_url
  return def || '（留空使用默认）'
})

const onTextProviderChange = () => {
  const def = TEXT_PROVIDER_DEFAULTS[textModel.value.provider]
  if (def) {
    if (!textModel.value.model || Object.values(TEXT_PROVIDER_DEFAULTS).some(d => d.model === textModel.value.model)) {
      textModel.value.model = def.model
    }
    if (!textModel.value.base_url || Object.values(TEXT_PROVIDER_DEFAULTS).some(d => d.base_url && d.base_url === textModel.value.base_url)) {
      textModel.value.base_url = def.base_url
    }
  }
}

const IMAGE_PROVIDER_DEFAULTS = {
  'seedream': { model: 'doubao-seedream-4-5-251128' },
  'wanx': { model: 'wanx2.1-t2i-turbo' },
  'qwen-image': { model: 'qwen-image-plus' },
}

const imageModel = ref({
  provider: 'seedream',
  model: 'doubao-seedream-4-5-251128',
  api_key: '',
  base_url: 'https://ark.cn-beijing.volces.com/api/v3',
  aspect_ratio: '16:9'
})

const onImageProviderChange = () => {
  const def = IMAGE_PROVIDER_DEFAULTS[imageModel.value.provider]
  if (def && def.model) {
    imageModel.value.model = def.model
  }
}

const videoModel = ref({
  provider: 'seedance',
  model: 'doubao-seedance-2-0-fast-260128',
  api_key: '',
  base_url: ''
})

// Video generation parameters (saved as ModelConfig.params JSON)
const videoParams = ref({
  duration: 15,
  resolution: '1080p',
  ratio: '16:9',
  generate_audio: true,
  watermark: false
})

// Cost estimate based on current params
const estimatedPrice = computed(() => {
  const isFast = (videoModel.value.model || '').includes('fast')
  const r = videoParams.value.resolution
  const d = videoParams.value.duration
  // Rough pricing for Seedance 2.0 (CNY per video)
  const baseRate = {'480p': 0.3, '720p': 0.6, '1080p': 1.3}[r] || 1.3  // per second
  const fastDiscount = isFast ? 0.55 : 1.0
  const total = baseRate * d * fastDiscount
  return `约 ¥${total.toFixed(2)} / 视频`
})

const priceFormula = computed(() => {
  const isFast = (videoModel.value.model || '').includes('fast')
  return `${videoParams.value.resolution} × ${videoParams.value.duration}s${isFast ? ' × Fast 折扣' : ''}`
})

const voiceModel = ref({
  provider: 'cosyvoice',
  model: 'qwen3-tts-flash',
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
      modelConfigApi.updateOrCreate({
        name: 'text',
        provider: textModel.value.provider,
        model: textModel.value.model,
        api_key: textModel.value.api_key,
        base_url: textModel.value.base_url || null,
        params: { temperature: Number(textModel.value.temperature) }
      }),
      modelConfigApi.updateOrCreate({
        name: 'image',
        provider: imageModel.value.provider,
        model: imageModel.value.model,
        api_key: imageModel.value.api_key,
        base_url: imageModel.value.base_url || null,
        params: { aspect_ratio: imageModel.value.aspect_ratio }
      }),
      modelConfigApi.updateOrCreate({
        name: 'video',
        provider: videoModel.value.provider,
        model: videoModel.value.model,
        api_key: videoModel.value.api_key,
        base_url: videoModel.value.base_url || null,
        params: { ...videoParams.value }
      }),
      modelConfigApi.updateOrCreate({
        name: 'voice',
        provider: voiceModel.value.provider,
        model: voiceModel.value.model,
        api_key: voiceModel.value.api_key,
        params: { stability: voiceModel.value.stability }
      })
    ])
    alert('配置已保存')
  } catch (error) {
    console.error(error)
    alert('保存失败：' + (error.response?.data?.detail || error.message))
  }
}

onMounted(async () => {
  try {
    const response = await modelConfigApi.getAll()
    response.data.forEach(config => {
      const p = config.params || {}
      if (config.name === 'text') {
        textModel.value = {
          ...textModel.value,
          provider: config.provider, model: config.model, api_key: config.api_key,
          base_url: config.base_url || '',
          temperature: p.temperature ?? textModel.value.temperature
        }
      } else if (config.name === 'image') {
        imageModel.value = {
          ...imageModel.value,
          provider: config.provider, model: config.model, api_key: config.api_key,
          base_url: config.base_url || imageModel.value.base_url,
          aspect_ratio: p.aspect_ratio ?? imageModel.value.aspect_ratio
        }
      } else if (config.name === 'video') {
        videoModel.value = {
          ...videoModel.value,
          provider: config.provider, model: config.model, api_key: config.api_key,
          base_url: config.base_url || ''
        }
        videoParams.value = {
          duration: p.duration ?? videoParams.value.duration,
          resolution: p.resolution ?? videoParams.value.resolution,
          ratio: p.ratio ?? videoParams.value.ratio,
          generate_audio: p.generate_audio ?? videoParams.value.generate_audio,
          watermark: p.watermark ?? videoParams.value.watermark
        }
      } else if (config.name === 'voice') {
        voiceModel.value = {
          ...voiceModel.value,
          provider: config.provider, model: config.model, api_key: config.api_key,
          stability: p.stability ?? voiceModel.value.stability
        }
      }
    })
  } catch (error) {
    console.error('Failed to load config:', error)
  }
})
</script>
