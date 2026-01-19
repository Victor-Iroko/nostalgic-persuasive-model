import { db } from '~~/server/utils/db'
import { contentFeedback } from '~~/server/database/schema'
import { z } from 'zod'
import { nanoid } from 'nanoid'
import { requireAuth } from '~~/server/utils/session'

const bodySchema = z.object({
  contentType: z.enum(['song', 'movie']),
  contentId: z.string(),
  // Interaction fields
  interactionType: z
    .enum(['view', 'click', 'skip', 'next', 'replay', 'feedback'])
    .default('feedback'),
  durationSeconds: z.number().optional(),
  // Feedback specific (optional now)
  bringsBackMemories: z.boolean().optional(),
  // Optional fields for enhanced reward calculation
  stressBefore: z.number().min(0).max(1).optional(),
  stressAfter: z.number().min(0).max(1).optional(),
  habitCompleted: z.boolean().optional(),
  journalText: z.string().optional(),
  contentYear: z.number().optional(),
  contentGenre: z.string().optional(),
})

export default defineEventHandler(async (event) => {
  const user = await requireAuth(event)
  const body = await readValidatedBody(event, bodySchema.parse)

  // Store interaction/feedback in database
  const [feedback] = await db
    .insert(contentFeedback)
    .values({
      id: nanoid(),
      userId: user.id,
      contentType: body.contentType,
      contentId: body.contentId,
      interactionType: body.interactionType,
      durationSeconds: body.durationSeconds,
      bringsBackMemories: body.bringsBackMemories,
    })
    .returning()

  // Only update the bandit model if it's explicit feedback
  // This ensures we don't skew the model with passive views/skips unless explicitly intended later
  if (body.interactionType === 'feedback' && body.bringsBackMemories !== undefined) {
    const config = useRuntimeConfig()
    const fastApiUrl = config.fastApiUrl || 'http://localhost:8000'

    try {
      await $fetch(`${fastApiUrl}/recommend/feedback`, {
        method: 'POST',
        body: {
          user_id: user.id,
          content_type: body.contentType,
          content_id: body.contentId,
          brings_back_memories: body.bringsBackMemories,
          stress_before: body.stressBefore,
          stress_after: body.stressAfter,
          habit_completed: body.habitCompleted,
          journal_text: body.journalText,
          content_year: body.contentYear,
          content_genre: body.contentGenre,
        },
      })
    } catch (error) {
      // Log but don't fail - feedback is already stored in DB
      console.error('Failed to update bandit model:', error)
    }
  }

  return { feedback, message: 'Interaction recorded' }
})
