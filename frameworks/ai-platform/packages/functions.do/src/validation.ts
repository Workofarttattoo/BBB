/**
 * Schema validation utilities
 */

import { z } from 'zod'
import Ajv from 'ajv'
import addFormats from 'ajv-formats'
import type { Schema } from './types'

// Initialize Ajv
const ajv = new Ajv({
  allErrors: true,
  strict: false,
  useDefaults: true,
})
addFormats(ajv)

// Cache for compiled validators
const validatorCache = new WeakMap<object, any>()

/**
 * Check if schema is Zod schema
 */
function isZodSchema(schema: Schema): schema is z.ZodType {
  return typeof schema === 'object' && '_def' in schema
}

/**
 * Get or compile validator for a JSON schema
 */
function getValidator(schema: object) {
  let validate = validatorCache.get(schema)
  if (!validate) {
    validate = ajv.compile(schema)
    validatorCache.set(schema, validate)
  }
  return validate
}

/**
 * Internal validation logic
 */
function validateSchema<T>(schema: Schema<T>, data: unknown): T {
  if (isZodSchema(schema)) {
    return schema.parse(data)
  }

  // JSON Schema validation
  const validate = getValidator(schema as object)
  const valid = validate(data)

  if (!valid) {
    throw new Error(
      `Validation failed: ${validate.errors?.map((e: any) => `${e.instancePath} ${e.message}`).join(', ')}`,
    )
  }

  return data as T
}

/**
 * Validate input against schema
 */
export function validateInput<T>(schema: Schema<T>, input: unknown): T {
  return validateSchema(schema, input)
}

/**
 * Validate output against schema
 */
export function validateOutput<T>(schema: Schema<T>, output: unknown): T {
  return validateSchema(schema, output)
}
