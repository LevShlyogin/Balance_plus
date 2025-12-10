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
  
 <!-- Скрипт оставляем без изменений -->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const props = defineProps<{ taskIid: number, projectId: number }>()
const emit = defineEmits(['back'])

const saving = ref(false)
const iframeRef = ref<HTMLIFrameElement | null>(null)
// ВАЖНО: Убедитесь, что IP правильный
const EXTERNAL_APP_URL = 'http://10.202.220.143:5252' 

const iframeSrc = computed(() => {
  return `${EXTERNAL_APP_URL}?taskId=${props.taskIid}&projectId=${props.projectId}&embedded=true`
})

// 1. Функция загрузки данных
const restoreState = async () => {
  try {
    const res = await axios.get('/api/v1/calculations/latest', {
      params: { task_iid: props.taskIid, project_id: props.projectId, app_type: 'valves' }
    })
    
    if (res.data.found) {
      console.log("✅ Найдены сохраненные данные, отправляем в приложение...")
      
      // Отправляем данные в Iframe
      const message = {
        type: 'WSA_RESTORE_STATE',
        payload: {
          input: res.data.input_data,
          output: res.data.output_data
        }
      }
      
      // Важно: отправляем только когда iframe загрузился
      iframeRef.value?.contentWindow?.postMessage(message, '*')
    }
  } catch (e) {
    console.warn("Нет сохраненных данных или ошибка:", e)
  }
}

// 2. Слушаем, когда Iframe скажет "Я готов"
const handleMessage = async (event: MessageEvent) => {
  const { type, payload } = event.data

  // Новое событие: приложение загрузилось
  if (type === 'WSA_READY') {
    await restoreState()
  }

  if (type === 'WSA_CALCULATION_COMPLETE') {
    await saveResult(payload)
  }
  
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
    alert(`✅ Результаты сохранены в задачу #${props.taskIid}!`)
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
  display: flex; /* Убирает лишние отступы снизу iframe */
  position: relative;
}

.app-frame { 
  width: 100%; 
  height: 100%; 
  border: none; /* Убираем рамку */
  display: block;
}

/* Красивый оверлей загрузки */
.overlay { 
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
  background: rgba(255,255,255,0.9); 
  display: flex; justify-content: center; align-items: center;
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
  width: 40px; height: 40px; margin: 0 auto 15px;
  border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>