/**
 * Go-style error handling pattern
 * Returns [error, data] tuple for explicit error handling
 */
export async function catchError<T>(
  promiseOrValue: Promise<T> | T,
  errorsToCatch?: Array<new (...args: unknown[]) => Error>
): Promise<[Error | undefined, T | undefined]> {
  try {
    const data = await Promise.resolve(promiseOrValue)
    return [undefined, data]
  } catch (err) {
    if (
      errorsToCatch === undefined ||
      errorsToCatch.some((E) => err instanceof E)
    ) {
      return [err as Error, undefined]
    }
    throw err // re-throw unexpected errors
  }
}

/**
 * Result type for functional error handling
 * Provides type-safe success/failure discrimination
 */
export type Result<T, E = Error> = 
  | { ok: true; data: T } 
  | { ok: false; error: E }

export function ok<T>(data: T): Result<T, never> {
  return { ok: true, data }
}

export function err<E>(error: E): Result<never, E> {
  return { ok: false, error }
}

/**
 * Wraps an async function to return a Result type
 */
export async function tryCatch<T, E = Error>(
  fn: () => Promise<T> | T
): Promise<Result<T, E>> {
  try {
    const data = await fn()
    return ok(data)
  } catch (error) {
    return err(error as E)
  }
}
