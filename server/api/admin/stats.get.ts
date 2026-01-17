import { db } from '~~/server/utils/db'
import { requireAdmin } from '~~/server/utils/admin'
import { user, userPreferences, dailyHabitLogs, contentFeedback } from '~~/server/database/schema'
import { sql, count, avg, eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  requireAdmin(event)

  // Get user counts by group
  const groupCounts = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      count: count(),
    })
    .from(userPreferences)
    .groupBy(userPreferences.experimentGroup)

  // Get total users
  const [totalUsers] = await db.select({ count: count() }).from(user)

  // Get total habit logs
  const [totalLogs] = await db.select({ count: count() }).from(dailyHabitLogs)

  // Get average stress by group
  const stressByGroup = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      avgStress: avg(dailyHabitLogs.stressLevel),
      logCount: count(),
    })
    .from(dailyHabitLogs)
    .innerJoin(userPreferences, eq(dailyHabitLogs.userId, userPreferences.userId))
    .groupBy(userPreferences.experimentGroup)

  // Get habit completion rate by group
  const completionByGroup = await db
    .select({
      experimentGroup: userPreferences.experimentGroup,
      totalLogs: count(),
      completedLogs: sql<number>`sum(case when ${dailyHabitLogs.completed} then 1 else 0 end)`,
    })
    .from(dailyHabitLogs)
    .innerJoin(userPreferences, eq(dailyHabitLogs.userId, userPreferences.userId))
    .groupBy(userPreferences.experimentGroup)

  // Get content feedback stats (treatment only)
  const [feedbackStats] = await db
    .select({
      totalFeedback: count(),
      positiveFeedback: sql<number>`sum(case when ${contentFeedback.bringsBackMemories} then 1 else 0 end)`,
    })
    .from(contentFeedback)

  // Format response
  const treatmentCount = groupCounts.find((g) => g.experimentGroup === 'treatment')?.count ?? 0
  const controlCount = groupCounts.find((g) => g.experimentGroup === 'control')?.count ?? 0

  const treatmentStress = stressByGroup.find((g) => g.experimentGroup === 'treatment')
  const controlStress = stressByGroup.find((g) => g.experimentGroup === 'control')

  const treatmentCompletion = completionByGroup.find((g) => g.experimentGroup === 'treatment')
  const controlCompletion = completionByGroup.find((g) => g.experimentGroup === 'control')

  return {
    overview: {
      totalUsers: totalUsers?.count ?? 0,
      treatmentUsers: treatmentCount,
      controlUsers: controlCount,
      totalHabitLogs: totalLogs?.count ?? 0,
    },
    stressComparison: {
      treatment: {
        avgStress: treatmentStress?.avgStress ? Number(treatmentStress.avgStress) : null,
        logCount: treatmentStress?.logCount ?? 0,
      },
      control: {
        avgStress: controlStress?.avgStress ? Number(controlStress.avgStress) : null,
        logCount: controlStress?.logCount ?? 0,
      },
    },
    completionComparison: {
      treatment: {
        total: treatmentCompletion?.totalLogs ?? 0,
        completed: treatmentCompletion?.completedLogs ?? 0,
        rate:
          treatmentCompletion?.totalLogs && treatmentCompletion.totalLogs > 0
            ? (Number(treatmentCompletion.completedLogs) / treatmentCompletion.totalLogs) * 100
            : 0,
      },
      control: {
        total: controlCompletion?.totalLogs ?? 0,
        completed: controlCompletion?.completedLogs ?? 0,
        rate:
          controlCompletion?.totalLogs && controlCompletion.totalLogs > 0
            ? (Number(controlCompletion.completedLogs) / controlCompletion.totalLogs) * 100
            : 0,
      },
    },
    nostalgiaFeedback: {
      total: feedbackStats?.totalFeedback ?? 0,
      positive: feedbackStats?.positiveFeedback ?? 0,
      positiveRate:
        feedbackStats?.totalFeedback && feedbackStats.totalFeedback > 0
          ? (Number(feedbackStats.positiveFeedback) / feedbackStats.totalFeedback) * 100
          : 0,
    },
  }
})
