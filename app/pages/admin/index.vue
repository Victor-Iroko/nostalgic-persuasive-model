<script setup lang="ts">
definePageMeta({
  layout: 'default',
  auth: false, // Uses custom admin auth
})

const router = useRouter()

// Types
interface StatsData {
  overview: {
    totalUsers: number
    treatmentUsers: number
    controlUsers: number
    totalHabitLogs: number
  }
  stressComparison: {
    treatment: { avgStress: number | null; logCount: number }
    control: { avgStress: number | null; logCount: number }
  }
  completionComparison: {
    treatment: { total: number; completed: number; rate: number }
    control: { total: number; completed: number; rate: number }
  }
  nostalgiaFeedback: {
    total: number
    positive: number
    positiveRate: number
  }
}

interface GroupComparison {
  emotions: {
    treatment: Record<string, number>
    control: Record<string, number>
  }
  stressDistribution: {
    treatment: { low: number; medium: number; high: number }
    control: { low: number; medium: number; high: number }
  }
}

// Fetch data
const {
  data: stats,
  error: statsError,
  refresh: refreshStats,
} = await useFetch<StatsData>('/api/admin/stats', {
  lazy: true,
  onResponseError: ({ response }) => {
    if (response.status === 401) {
      router.push('/admin/login')
    }
  },
})

const { data: comparison, refresh: refreshComparison } = await useFetch<GroupComparison>(
  '/api/admin/group-comparison',
  { lazy: true }
)

// Check auth on mount
onMounted(() => {
  if (statsError.value?.statusCode === 401) {
    router.push('/admin/login')
  }
})

// Logout
async function handleLogout() {
  await $fetch('/api/admin/logout', { method: 'POST' })
  router.push('/admin/login')
}

// Export CSV
function exportCsv() {
  window.open('/api/admin/export-csv', '_blank')
}

// Refresh all data
async function refreshData() {
  await Promise.all([refreshStats(), refreshComparison()])
}

// Format percentage
function formatPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  return `${value.toFixed(1)}%`
}

// Format stress
function formatStress(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  return value.toFixed(3)
}

// Get all unique emotions
const allEmotions = computed(() => {
  if (!comparison.value) return []
  const emotions = new Set([
    ...Object.keys(comparison.value.emotions.treatment),
    ...Object.keys(comparison.value.emotions.control),
  ])
  return Array.from(emotions).sort()
})
</script>

<template>
  <UContainer class="space-y-6 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold">Admin Dashboard</h1>
        <p class="mt-1 text-muted">Research analytics & group comparison</p>
      </div>
      <div class="flex items-center gap-3">
        <UButton color="neutral" variant="soft" icon="i-lucide-refresh-cw" @click="refreshData">
          Refresh
        </UButton>
        <UButton color="primary" icon="i-lucide-download" @click="exportCsv"> Export CSV </UButton>
        <UButton color="neutral" variant="ghost" icon="i-lucide-log-out" @click="handleLogout">
          Logout
        </UButton>
      </div>
    </div>

    <!-- Overview Stats -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Total Users</p>
          <p class="text-3xl font-bold">{{ stats?.overview.totalUsers ?? '—' }}</p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Nostalgia Group</p>
          <p class="text-3xl font-bold text-amber-500">
            {{ stats?.overview.treatmentUsers ?? '—' }}
          </p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Control Group</p>
          <p class="text-3xl font-bold text-slate-500">
            {{ stats?.overview.controlUsers ?? '—' }}
          </p>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <p class="text-sm text-muted">Total Habit Logs</p>
          <p class="text-3xl font-bold">{{ stats?.overview.totalHabitLogs ?? '—' }}</p>
        </div>
      </UCard>
    </div>

    <!-- Stress Comparison -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-brain" class="text-xl text-purple-500" />
          <h2 class="text-lg font-semibold">Stress Level Comparison</h2>
        </div>
      </template>

      <div class="grid gap-6 md:grid-cols-2">
        <!-- Nostalgia Group -->
        <div class="rounded-lg bg-amber-500/10 p-4">
          <h3 class="mb-3 font-semibold text-amber-600">Nostalgia Group</h3>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-sm">Average Stress</span>
              <span class="font-mono font-medium">
                {{ formatStress(stats?.stressComparison.treatment.avgStress) }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm">Logs with Stress Data</span>
              <span class="font-medium">{{ stats?.stressComparison.treatment.logCount ?? 0 }}</span>
            </div>
            <div class="mt-3 flex gap-2">
              <div class="flex-1 rounded bg-green-500/20 p-2 text-center">
                <p class="text-xs text-muted">Low</p>
                <p class="font-bold text-green-600">
                  {{ comparison?.stressDistribution.treatment.low ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-yellow-500/20 p-2 text-center">
                <p class="text-xs text-muted">Medium</p>
                <p class="font-bold text-yellow-600">
                  {{ comparison?.stressDistribution.treatment.medium ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-red-500/20 p-2 text-center">
                <p class="text-xs text-muted">High</p>
                <p class="font-bold text-red-600">
                  {{ comparison?.stressDistribution.treatment.high ?? 0 }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Control Group -->
        <div class="rounded-lg bg-slate-500/10 p-4">
          <h3 class="mb-3 font-semibold text-slate-600">Control Group</h3>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-sm">Average Stress</span>
              <span class="font-mono font-medium">
                {{ formatStress(stats?.stressComparison.control.avgStress) }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm">Logs with Stress Data</span>
              <span class="font-medium">{{ stats?.stressComparison.control.logCount ?? 0 }}</span>
            </div>
            <div class="mt-3 flex gap-2">
              <div class="flex-1 rounded bg-green-500/20 p-2 text-center">
                <p class="text-xs text-muted">Low</p>
                <p class="font-bold text-green-600">
                  {{ comparison?.stressDistribution.control.low ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-yellow-500/20 p-2 text-center">
                <p class="text-xs text-muted">Medium</p>
                <p class="font-bold text-yellow-600">
                  {{ comparison?.stressDistribution.control.medium ?? 0 }}
                </p>
              </div>
              <div class="flex-1 rounded bg-red-500/20 p-2 text-center">
                <p class="text-xs text-muted">High</p>
                <p class="font-bold text-red-600">
                  {{ comparison?.stressDistribution.control.high ?? 0 }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Emotion Comparison -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-smile" class="text-xl text-pink-500" />
          <h2 class="text-lg font-semibold">Emotion Distribution</h2>
        </div>
      </template>

      <div v-if="allEmotions.length === 0" class="py-8 text-center text-muted">
        No emotion data available yet
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b">
              <th class="py-2 text-left font-medium">Emotion</th>
              <th class="py-2 text-right font-medium text-amber-600">Nostalgia</th>
              <th class="py-2 text-right font-medium text-slate-600">Control</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="emotion in allEmotions" :key="emotion" class="border-b border-default">
              <td class="py-2">{{ emotion }}</td>
              <td class="py-2 text-right font-mono">
                {{ comparison?.emotions.treatment[emotion] ?? 0 }}
              </td>
              <td class="py-2 text-right font-mono">
                {{ comparison?.emotions.control[emotion] ?? 0 }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>

    <!-- Completion & Feedback -->
    <div class="grid gap-6 md:grid-cols-2">
      <!-- Habit Completion -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-check-circle" class="text-xl text-green-500" />
            <h2 class="text-lg font-semibold">Habit Completion</h2>
          </div>
        </template>

        <div class="space-y-4">
          <div class="flex items-center justify-between rounded-lg bg-amber-500/10 p-3">
            <span class="font-medium text-amber-600">Nostalgia</span>
            <div class="text-right">
              <span class="text-2xl font-bold">
                {{ formatPct(stats?.completionComparison.treatment.rate) }}
              </span>
              <p class="text-xs text-muted">
                {{ stats?.completionComparison.treatment.completed ?? 0 }} /
                {{ stats?.completionComparison.treatment.total ?? 0 }} logs
              </p>
            </div>
          </div>
          <div class="flex items-center justify-between rounded-lg bg-slate-500/10 p-3">
            <span class="font-medium text-slate-600">Control</span>
            <div class="text-right">
              <span class="text-2xl font-bold">
                {{ formatPct(stats?.completionComparison.control.rate) }}
              </span>
              <p class="text-xs text-muted">
                {{ stats?.completionComparison.control.completed ?? 0 }} /
                {{ stats?.completionComparison.control.total ?? 0 }} logs
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Nostalgia Feedback -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-sparkles" class="text-xl text-amber-500" />
            <h2 class="text-lg font-semibold">Nostalgia Feedback</h2>
          </div>
        </template>

        <div class="space-y-4">
          <div class="text-center">
            <p class="text-sm text-muted">Positive Response Rate</p>
            <p class="text-4xl font-bold text-amber-500">
              {{ formatPct(stats?.nostalgiaFeedback.positiveRate) }}
            </p>
          </div>
          <div class="flex justify-center gap-8">
            <div class="text-center">
              <p class="text-2xl font-bold text-green-500">
                {{ stats?.nostalgiaFeedback.positive ?? 0 }}
              </p>
              <p class="text-xs text-muted">"Brings back memories"</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-slate-400">
                {{
                  (stats?.nostalgiaFeedback.total ?? 0) - (stats?.nostalgiaFeedback.positive ?? 0)
                }}
              </p>
              <p class="text-xs text-muted">"Not really"</p>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </UContainer>
</template>
