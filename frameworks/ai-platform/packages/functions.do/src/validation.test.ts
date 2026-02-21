import { describe, it, expect } from 'vitest'
import { z } from 'zod'
import { validateInput, validateOutput } from './validation'

describe('validation', () => {
  describe('Zod Schema', () => {
    const schema = z.object({
      name: z.string(),
      age: z.number(),
    })

    it('should validate valid input', () => {
      const input = { name: 'John', age: 30 }
      expect(validateInput(schema, input)).toEqual(input)
    })

    it('should throw on invalid input', () => {
      const input = { name: 'John', age: '30' }
      expect(() => validateInput(schema, input)).toThrow()
    })
  })

  describe('JSON Schema', () => {
    const schema = {
      type: 'object',
      properties: {
        name: { type: 'string' },
        age: { type: 'number' },
      },
      required: ['name', 'age'],
    }

    it('should validate valid input', () => {
      const input = { name: 'John', age: 30 }
      expect(validateInput(schema as any, input)).toEqual(input)
    })

    it('should throw on invalid input', () => {
      const input = { name: 'John', age: '30' }
      expect(() => validateInput(schema as any, input)).toThrow(/Input validation failed/)
    })

    it('should throw on missing required fields', () => {
      const input = { name: 'John' }
      expect(() => validateInput(schema as any, input)).toThrow(/must have required property 'age'/)
    })

    it('should use defaults if specified', () => {
      const schemaWithDefault = {
        type: 'object',
        properties: {
          name: { type: 'string' },
          role: { type: 'string', default: 'user' },
        },
        required: ['name'],
      }
      const input = { name: 'John' }
      const validated = validateInput(schemaWithDefault as any, input)
      expect(validated).toEqual({ name: 'John', role: 'user' })
    })
  })

  describe('validateOutput', () => {
    const schema = z.string()

    it('should validate valid output', () => {
      expect(validateOutput(schema, 'success')).toBe('success')
    })

    it('should throw on invalid output', () => {
      expect(() => validateOutput(schema, 123)).toThrow()
    })

    it('should validate JSON Schema output', () => {
      const jsonSchema = { type: 'number' }
      expect(validateOutput(jsonSchema as any, 123)).toBe(123)
      expect(() => validateOutput(jsonSchema as any, '123')).toThrow(/Output validation failed/)
    })
  })
})
