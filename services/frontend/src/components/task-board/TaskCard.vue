<template>
  <div class="task-card" @click="$emit('click')">
    <div class="card-header">
      <div class="header-top">
        <!-- Показываем Проект (Т-150) -->
        <span class="turbine-badge" v-if="task.turbine_project !== 'Без проекта'">
          {{ task.turbine_project }}
        </span>
        <span v-else class="turbine-badge empty">--</span>

        <span :class="['status-dot', task.state]" :title="task.status_rus"></span>
      </div>
      <h3 class="card-title">{{ task.title }}</h3>
    </div>

    <p class="card-desc">
      {{ task.description || 'Нет описания' }}
    </p>

    <div class="card-footer">
      <div class="meta-row">
        <span class="meta-label">Создано:</span>
        <span class="meta-value">{{ task.formatted_date }}</span>
      </div>
      
      <!-- Срок сдачи -->
      <div class="meta-row" v-if="task.due_date">
        <span class="meta-label">Срок:</span>
        <!-- Форматируем дату ISO YYYY-MM-DD в DD.MM.YY -->
        <span class="meta-value overdue">{{ formatDate(task.due_date) }}</span>
      </div>
      
      <div class="tags-row">
        <!-- Тип расчёта (Человеческое название) -->
        <span class="tag type-tag">{{ task.calc_type_human }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ task: any }>()
defineEmits(['click'])

// Простая функция форматирования даты на фронте
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' })
}
</script>

<style scoped>
.task-card {
  background: #F2F2F2;
  padding: 16px;
  height: 230px;
  display: flex; flex-direction: column; justify-content: space-between;
  cursor: pointer; border-radius: 4px;
  transition: transform 0.1s, box-shadow 0.1s;
  box-sizing: border-box; /* Важно для отступов */
}
.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  background: #e8e8e8;
}

.header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.turbine-badge {
  font-size: 12px; font-weight: 700; color: #444; text-transform: uppercase;
  background: #d1d1d1; padding: 2px 6px; border-radius: 4px;
}
.turbine-badge.empty { opacity: 0.5; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #28a745; }
.status-dot.closed { background: #dc3545; }

.card-title { margin: 0; font-weight: 600; font-size: 18px; line-height: 1.2; }

.card-desc {
  font-size: 14px; line-height: 1.4; color: #333;
  flex-grow: 1; margin: 12px 0;
  overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
}

.meta-row { display: flex; gap: 6px; font-size: 13px; margin-bottom: 4px; }
.meta-label { color: #888; }
.meta-value { color: #000; font-weight: 500; }
.meta-value.overdue { color: #d32f2f; }

.tags-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.tag { font-size: 11px; padding: 3px 8px; border-radius: 10px; }
.type-tag { background: #e3f2fd; color: #0d47a1; border: 1px solid #bbdefb; }
</style>