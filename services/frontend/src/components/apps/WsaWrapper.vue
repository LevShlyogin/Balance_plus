<template>
  <div class="iframe-container">
    <div v-if="saving" class="overlay">
      <div class="loader-box">
        <div class="spinner"></div>
        <p>💾 Сохранение результатов в GitLab...</p>
      </div>
    </div>

    <iframe
        ref="iframeRef"
        :src="iframeSrc"
        class="app-frame"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, onUnmounted} from 'vue'
import axios from 'axios'

const props = defineProps<{ taskIid: number, projectId: number }>()
const emit = defineEmits(['back'])

const saving = ref(false)
const iframeRef = ref<HTMLIFrameElement | null>(null)

// ВАЖНО: Это адрес, где запущен фронтенд штоков (Stock Calc)
const EXTERNAL_APP_URL = 'http://10.202.220.143:5252/calculator'

const iframeSrc = computed(() => {
  // Добавляем timestamp, чтобы избежать кеширования iframe
  return `${EXTERNAL_APP_URL}?taskId=${props.taskIid}&projectId=${props.projectId}&embedded=true`
})

// 1. Функция загрузки данных
const restoreState = async () => {
  try {
    const res = await axios.get('/api/v1/calculations/latest', {
      params: {task_iid: props.taskIid, project_id: props.projectId, app_type: 'valves'}
    })

    if (res.data && res.data.found) {
      console.log("✅ Найдены сохраненные данные, отправляем в приложение...")

      // Отправляем данные в Iframe
      const message = {
        type: 'WSA_RESTORE_STATE',
        payload: {
          input: res.data.input_data,
          output: res.data.output_data
        }
      }

      // Отправляем сообщение внутрь iframe
      iframeRef.value?.contentWindow?.postMessage(message, '*')
    } else {
      console.log("ℹ️ Сохраненных данных нет, начинаем с чистого листа.")
    }
  } catch (e) {
    console.warn("Ошибка при проверке сохраненных данных:", e)
  }
}

// 2. Слушаем сообщения от Iframe
const handleMessage = async (event: MessageEvent) => {
  // Проверка origin (опционально, для безопасности в будущем)
  // if (event.origin !== new URL(EXTERNAL_APP_URL).origin) return;

  const {type, payload} = event.data

  // Приложение загрузилось и готово
  if (type === 'WSA_READY') {
    console.log("🔹 Iframe готов (WSA_READY), пробуем восстановить состояние...")
    await restoreState()
  }

  // Приложение закончило расчет
  if (type === 'WSA_CALCULATION_COMPLETE') {
    await saveResult(payload)
  }

  // Приложение просит закрыться
  if (type === 'WSA_CLOSE') {
    emit('back')
  }
}

const saveResult = async (data: any) => {
  saving.value = true
  try {
    const requestPayload = {
      task_iid: props.taskIid,
      project_id: props.projectId,
      app_type: 'valves',
      input_data: data.input,
      output_data: data.output,
      commit_message: `Расчёт из приложения`
    }

    await axios.post('/api/v1/calculations/save', requestPayload)
    // alert убираем, так как toast есть внутри iframe, здесь просто лог
    console.log(`✅ Результаты сохранены в задачу #${props.taskIid}!`)
  } catch (e: any) {
    alert('Ошибка сохранения: ' + e.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => window.addEventListener('message', handleMessage))
onUnmounted(() => window.removeEventListener('message', handleMessage))
</script>

<style scoped>
.iframe-container {
  width: 100%;
  height: 100%;
  display: flex;
  position: relative;
}

.app-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  backdrop-filter: blur(2px);
}

.loader-box {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 15px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>