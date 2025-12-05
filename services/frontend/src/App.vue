<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

import Header from './components/layout/Header.vue'
import TaskCard from './components/task-board/TaskCard.vue'
import NewTaskCard from './components/task-board/NewTaskCard.vue'
import CreateTaskModal from './components/task-board/CreateTaskModal.vue'
import WsaWrapper from './components/apps/WsaWrapper.vue'

// --- ТИПЫ ---
interface Task {
  iid: number
  title: string
  description?: string
  formatted_date: string
  calc_type: string
  turbine_project: string
  labels: string[]
  state: string
  due_date?: string
}

// --- CONSTANTS ---
const TABS = [
  { id: 'all', label: 'Все задачи', tag: null },
  { id: 'valves', label: 'Штоки клапанов', tag: 'valves' },
  { id: 'balance', label: 'Балансы', tag: 'balance' },
  { id: 'triangles', label: 'Треугольники скоростей', tag: 'triangles' },
  { id: 'thermal', label: 'Тепловые расчёты', tag: 'thermal' },
  { id: 'strength', label: 'Прочность', tag: 'strength' },
  { id: 'vibration', label: 'Вибрация', tag: 'vibration' },
]

// --- STATE ---
const currentUser = ref({ name: 'Загрузка...', avatar_url: '' })
const tasks = ref<Task[]>([])
const activeTabId = ref('all')
const showCreateModal = ref(false)
const searchQuery = ref('')
const loading = ref(true)
const sortOrder = ref<'desc' | 'asc'>('desc')

const activeView = ref<'dashboard' | 'app-valves'>('dashboard')
const currentTaskIid = ref(0)

// --- API ---
const fetchData = async () => {
  try {
    const [userRes, tasksRes] = await Promise.all([
      axios.get('/api/v1/user/me'),
      axios.get('/api/v1/tasks?state=opened')
    ])
    currentUser.value = userRes.data
    tasks.value = tasksRes.data
  } catch (e) { console.error(e) } 
  finally { loading.value = false }
}

const createTask = async (data: any) => {
  try {
    await axios.post('/api/v1/tasks', {
      title: data.title,
      description: data.description,
      labels: data.labels
    })
    showCreateModal.value = false
    await fetchData()
  } catch (e: any) {
    alert('Ошибка: ' + e.message)
  }
}

const handleTaskClick = (task: Task) => {
  if (task.calc_type === 'valves' || task.labels.includes('valves') || task.title.toLowerCase().includes('шток')) {
    if (!confirm(`Открыть приложение "Расчёт штоков" для задачи #${task.iid}?`)) return;
    currentTaskIid.value = task.iid
    activeView.value = 'app-valves'
  } else {
    alert(`Для типа "${task.calc_type}" интерфейс еще не готов.`)
  }
}

// --- COMPUTED ---
const filteredTasks = computed(() => {
  let result = [...tasks.value]
  const activeTab = TABS.find(t => t.id === activeTabId.value)
  if (activeTab && activeTab.tag) {
    result = result.filter(t => t.calc_type === activeTab.tag)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => t.title.toLowerCase().includes(q) || t.turbine_project.toLowerCase().includes(q))
  }
  result.sort((a, b) => {
    const dateA = new Date(a.created_at).getTime()
    const dateB = new Date(b.created_at).getTime()
    return sortOrder.value === 'asc' ? dateA - dateB : dateB - dateA
  })
  return result
})

const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

onMounted(fetchData)
</script>

<template>
  <!-- Обертка layout должна быть всегда -->
  <div class="layout">
    
    <!-- БЛОК 1: ДАШБОРД -->
    <!-- v-show лучше чем v-if здесь, чтобы не терять скролл при возврате, но v-if надежнее для изоляции -->
    <div v-if="activeView === 'dashboard'" class="dashboard-wrapper">
      <Header :user="currentUser" />
      
      <main class="main-container">
        <nav class="main-nav">
          <a 
            v-for="tab in TABS" :key="tab.id" href="#" class="nav-link"
            :class="{ active: activeTabId === tab.id }"
            @click.prevent="activeTabId = tab.id"
          >
            {{ tab.label }}
          </a>
        </nav>

        <div class="actions-row">
          <div class="search-input">
            <span class="icon">🔍</span>
            <input v-model="searchQuery" type="text" placeholder="Поиск..." />
          </div>
          <button class="action-btn" @click="toggleSort"><span class="icon">⇅</span> Сортировка</button>
          <button class="action-btn primary" @click="fetchData">↻ Обновить</button>
        </div>

        <div class="task-grid">
          <NewTaskCard @click="showCreateModal = true" />
          <div v-if="loading">Загрузка...</div>
          <TaskCard 
            v-for="task in filteredTasks" :key="task.iid" :task="task"
            @click="handleTaskClick(task)"
          />
        </div>
      </main>
    </div>

    <!-- БЛОК 2: ПРИЛОЖЕНИЕ (ПОЛНЫЙ ЭКРАН ПОВЕРХ ВСЕГО) -->
    <div v-else-if="activeView === 'app-valves'" class="fullscreen-app">
      <WsaWrapper 
        :taskIid="currentTaskIid" 
        @back="activeView = 'dashboard'" 
      />
    </div>

    <CreateTaskModal v-if="showCreateModal" @close="showCreateModal = false" @create="createTask" />
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* === ГЛОБАЛЬНЫЙ СБРОС (Самое важное для фикса верстки) === */
*, *::before, *::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
  background-color: #FFFFFF;
  /* Возвращаем нормальный скролл для страницы */
  overflow-y: auto; 
  overflow-x: hidden;
}

.layout {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* === СТИЛИ ДАШБОРДА === */
.dashboard-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.top-bar { 
  width: 100%;
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  height: 56px; 
  padding: 0 32px; 
  border-bottom: 1px solid #E6E6E6; 
  background: #fff; 
}

.main-container { 
  width: 100%;
  max-width: 100%; /* Защита от вылезания */
  padding: 32px; 
  flex: 1;
}

.main-nav { 
  display: flex; 
  gap: 30px; 
  margin-bottom: 30px; 
  border-bottom: 1px solid #eee; 
  overflow-x: auto; /* Если меню длинное, добавляем скролл */
}

.nav-link { 
  text-decoration: none; color: #000; font-size: 16px; 
  padding-bottom: 12px; border-bottom: 2px solid transparent; 
  transition: all 0.2s; white-space: nowrap; 
}
.nav-link:hover { color: #666; }
.nav-link.active { font-weight: 600; color: #000; border-bottom: 2px solid #000; }

.actions-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }

.search-input { 
  flex-grow: 1; display: flex; align-items: center; 
  padding: 0 12px; height: 40px; border: 1px solid #D9D9D9; 
  border-radius: 4px; background: #fff; min-width: 200px; 
}
.search-input input { border: none; outline: none; width: 100%; font-size: 16px; font-family: inherit; }

.action-btn { 
  display: flex; align-items: center; justify-content: center; 
  padding: 0 20px; height: 40px; background: #F2F2F2; 
  border: none; border-radius: 4px; cursor: pointer; 
  font-size: 15px; font-family: inherit; gap: 8px; 
  transition: background 0.2s; white-space: nowrap;
}
.action-btn:hover { background: #e0e0e0; }
.action-btn.primary { background: #000; color: #fff; }
.action-btn.primary:hover { background: #333; }

.task-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); 
  gap: 24px; 
  padding-bottom: 50px; 
}

/* === СТИЛИ ПОЛНОЭКРАННОГО ПРИЛОЖЕНИЯ === */
.fullscreen-app {
  position: fixed; /* Фиксируем поверх всего */
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #fff;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Внутри приложения свои скроллы */
}
</style>