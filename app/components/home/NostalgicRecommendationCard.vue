<script setup lang="ts">
type Song = {
  id: string
  name: string
  albumName: string | null
  artists: string[] | null
  year: number | null
  genre: string | null
}

type Movie = {
  id: number
  title: string
  year: number | null
  genres: string[] | null
}

type Recommendation = {
  type: 'song' | 'movie'
  content: Song | Movie
}

const props = defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

// Fetch recommendation
const {
  data: recommendation,
  refresh,
  status,
} = await useFetch<Recommendation>('/api/habits/recommendation', { lazy: true })

const isLoading = computed(() => props.loading || status.value === 'pending')

// Feedback state
const feedbackSubmitted = ref(false)
const feedbackLoading = ref(false)

async function submitFeedback(bringsBackMemories: boolean) {
  if (!recommendation.value) return

  feedbackLoading.value = true
  try {
    await $fetch('/api/habits/feedback', {
      method: 'POST',
      body: {
        contentType: recommendation.value.type,
        contentId: String(
          recommendation.value.type === 'song'
            ? (recommendation.value.content as Song).id
            : (recommendation.value.content as Movie).id
        ),
        bringsBackMemories,
      },
    })
    feedbackSubmitted.value = true
  } catch (error) {
    console.error('Failed to submit feedback:', error)
  } finally {
    feedbackLoading.value = false
  }
}

async function handleRefresh() {
  feedbackSubmitted.value = false
  await refresh()
  emit('refresh')
}

// Helper to get display info
const displayInfo = computed(() => {
  if (!recommendation.value) return null

  if (recommendation.value.type === 'song') {
    const song = recommendation.value.content as Song
    return {
      type: 'song',
      icon: 'i-lucide-music',
      title: song.name,
      subtitle: song.artists?.join(', ') || 'Unknown Artist',
      year: song.year,
      meta: song.genre || song.albumName,
    }
  }

  const movie = recommendation.value.content as Movie
  return {
    type: 'movie',
    icon: 'i-lucide-film',
    title: movie.title,
    subtitle: movie.genres?.slice(0, 3).join(', ') || 'Movie',
    year: movie.year,
    meta: null,
  }
})
</script>

<template>
  <UCard class="nostalgic-card overflow-hidden">
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-sparkles" class="shrink-0 text-amber-500" />
          <h3 class="font-semibold whitespace-nowrap">Nostalgic Pick</h3>
        </div>
        <UButton
          color="neutral"
          variant="ghost"
          size="xs"
          icon="i-lucide-refresh-cw"
          :loading="isLoading"
          class="shrink-0"
          @click="handleRefresh"
        >
          <span class="hidden sm:inline">New Pick</span>
        </UButton>
      </div>
    </template>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-8">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-2xl text-muted" />
    </div>

    <!-- Content -->
    <div v-else-if="displayInfo" class="space-y-4">
      <div class="flex items-start gap-4">
        <div
          class="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20"
        >
          <UIcon :name="displayInfo.icon" class="text-3xl text-amber-600" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="mb-1 text-xs font-medium tracking-wide text-amber-600 uppercase">
            {{ displayInfo.type === 'song' ? '🎵 Song' : '🎬 Movie' }}
            <span v-if="displayInfo.year" class="text-muted"> • {{ displayInfo.year }}</span>
          </p>
          <h4 class="truncate text-lg font-semibold">{{ displayInfo.title }}</h4>
          <p class="truncate text-sm text-muted">{{ displayInfo.subtitle }}</p>
          <p v-if="displayInfo.meta" class="mt-1 text-xs text-muted">{{ displayInfo.meta }}</p>
        </div>
      </div>

      <!-- Feedback Section -->
      <div v-if="!feedbackSubmitted" class="border-t border-default pt-4">
        <p class="mb-3 text-sm text-muted">Does this bring back any memories?</p>
        <div class="flex gap-2">
          <UButton
            color="primary"
            variant="soft"
            size="sm"
            class="flex-1"
            :loading="feedbackLoading"
            @click="submitFeedback(true)"
          >
            🎯 Yes, it does!
          </UButton>
          <UButton
            color="neutral"
            variant="soft"
            size="sm"
            class="flex-1"
            :loading="feedbackLoading"
            @click="submitFeedback(false)"
          >
            🤔 Not really
          </UButton>
        </div>
      </div>

      <!-- Feedback Submitted -->
      <div v-else class="border-t border-default pt-4">
        <p class="text-center text-sm text-muted">✓ Thanks for your feedback!</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else class="py-8 text-center text-muted">
      <p>No recommendations available</p>
      <UButton color="neutral" variant="ghost" size="sm" class="mt-2" @click="handleRefresh">
        Try again
      </UButton>
    </div>
  </UCard>
</template>

<style scoped>
.nostalgic-card {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.05), rgba(249, 115, 22, 0.05));
}
</style>
