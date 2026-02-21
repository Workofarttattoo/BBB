/**
 * Schema validation utilities
 */

import { z } from 'zod'
import Ajv from 'ajv'
import addFormats from 'ajv-formats'
import type { Schema } from './types'

// Initialize Ajv singleton
const ajv = new Ajv({
  allErrors: true,
  strict: false,
  useDefaults: true,
})
addFormats(ajv)

/**
 * Check if schema is Zod schema
 */
function isZodSchema(schema: Schema): schema is z.ZodType {
  return typeof schema === 'object' && schema !== null && '_def' in schema
}

/**
 * Validate input against schema
 */
export function validateInput<T>(schema: Schema<T>, input: unknown): T {
  if (isZodSchema(schema)) {
    return schema.parse(input)
  }

  // JSON Schema validation
  const validate = ajv.compile(schema as object)
  if (!validate(input)) {
    throw new Error(`Input validation failed: ${ajv.errorsText(validate.errors)}`)
  }

  return input as T
}

/**
 * Validate output against schema
 */
export function validateOutput<T>(schema: Schema<T>, output: unknown): T {
  if (isZodSchema(schema)) {
    return schema.parse(output)
  }

  // JSON Schema validation
  const validate = ajv.compile(schema as object)
  if (!validate(output)) {
    throw new Error(`Output validation failed: ${ajv.errorsText(validate.errors)}`)
  }

  return output as T
}
