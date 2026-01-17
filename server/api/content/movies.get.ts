import { db } from '~~/server/utils/db'
import { movies } from '~~/server/database/schema'
import { sql, ilike, and, gte, lte, notInArray, inArray, desc } from 'drizzle-orm'
import { z } from 'zod'

const querySchema = z.object({
  yearStart: z.coerce.number().optional(),
  yearEnd: z.coerce.number().optional(),
  search: z.string().optional(),
  limit: z.coerce.number().min(1).max(50).default(20),
  excludeIds: z.string().optional(),
  mode: z.enum(['random', 'popular', 'similar']).optional().default('random'),
  selectedIds: z.string().optional(),
})

export default defineEventHandler(async (event) => {
  const query = await getValidatedQuery(event, querySchema.parse)

  // Build common conditions
  const conditions = []
  if (query.yearStart) {
    conditions.push(gte(movies.year, query.yearStart))
  }
  if (query.yearEnd) {
    conditions.push(lte(movies.year, query.yearEnd))
  }
  if (query.search && query.search.trim()) {
    conditions.push(ilike(movies.title, `%${query.search.trim()}%`))
  }
  if (query.excludeIds) {
    const excludeList = query.excludeIds
      .split(',')
      .filter(Boolean)
      .map((id) => parseInt(id, 10))
    if (excludeList.length > 0) {
      conditions.push(notInArray(movies.id, excludeList))
    }
  }

  // Mode: similar - use FastAPI recommender
  if (query.mode === 'similar' && query.selectedIds) {
    const selectedList = query.selectedIds
      .split(',')
      .filter(Boolean)
      .map((id) => parseInt(id, 10))

    if (selectedList.length > 0) {
      try {
        const config = useRuntimeConfig()
        const fastApiUrl = config.fastApiUrl || 'http://localhost:8000'

        type MovieRecommendation = {
          movieId: number
          title: string
          genres: string
          decade: string
          score: number
        }
        const response = await $fetch<{ recommendations: MovieRecommendation[] }>(
          `${fastApiUrl}/movies/recommend`,
          {
            method: 'POST',
            body: { liked_movie_ids: selectedList, n_recommendations: query.limit },
          }
        )

        const movieIds = response.recommendations.map((r) => r.movieId)
        const results = await db
          .select({ id: movies.id, title: movies.title, year: movies.year, genres: movies.genres })
          .from(movies)
          .where(and(inArray(movies.id, movieIds), ...(conditions.length > 0 ? conditions : [])))
          .limit(query.limit)

        return { items: results, count: results.length, mode: 'similar' }
      } catch {
        // Fall back to popular if FastAPI fails
      }
    }
  }

  // Mode: popular - order by rating count descending
  if (query.mode === 'popular') {
    const results = await db
      .select({ id: movies.id, title: movies.title, year: movies.year, genres: movies.genres })
      .from(movies)
      .where(conditions.length > 0 ? and(...conditions) : undefined)
      .orderBy(desc(movies.ratingCount))
      .limit(query.limit)

    return { items: results, count: results.length, mode: 'popular' }
  }

  // Default: random
  const results = await db
    .select({ id: movies.id, title: movies.title, year: movies.year, genres: movies.genres })
    .from(movies)
    .where(conditions.length > 0 ? and(...conditions) : undefined)
    .orderBy(sql`RANDOM()`)
    .limit(query.limit)

  return { items: results, count: results.length, mode: 'random' }
})
