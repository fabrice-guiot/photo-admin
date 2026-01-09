/**
 * Tests for external ID utilities.
 *
 * Tests cover:
 * - External ID validation
 * - Entity type extraction
 * - Identifier type detection
 * - Format utilities
 */

import { describe, test, expect, vi } from 'vitest'
import {
  isValidExternalId,
  getEntityType,
  getPrefix,
  isNumericId,
  isExternalId,
  getIdentifierType,
  formatExternalId,
  copyExternalId,
  ENTITY_PREFIXES,
} from './externalId'

describe('isValidExternalId', () => {
  test('validates correct external IDs', () => {
    expect(isValidExternalId('col_01234567890abcdefghjkmnpqr')).toBe(true)
    expect(isValidExternalId('con_ABCDEFGHJKMNPQRSTVWXYZ0123')).toBe(true)
    expect(isValidExternalId('pip_01hgw2bbg0000000000000002')).toBe(true)
    expect(isValidExternalId('res_01HGW2BBG0000000000000003')).toBe(true)
  })

  test('validates case-insensitively', () => {
    expect(isValidExternalId('COL_01234567890ABCDEFGHJKMNPQR')).toBe(true)
    expect(isValidExternalId('Col_01234567890abcdefghjkmnpqr')).toBe(true)
  })

  test('validates with expected prefix', () => {
    expect(isValidExternalId('col_01234567890abcdefghjkmnpqr', 'col')).toBe(true)
    expect(isValidExternalId('col_01234567890abcdefghjkmnpqr', 'con')).toBe(false)
  })

  test('rejects invalid external IDs', () => {
    // Empty or null
    expect(isValidExternalId('')).toBe(false)
    expect(isValidExternalId(null as any)).toBe(false)
    expect(isValidExternalId(undefined as any)).toBe(false)

    // Wrong prefix
    expect(isValidExternalId('xxx_01234567890abcdefghjkmnpqr')).toBe(false)

    // Too short
    expect(isValidExternalId('col_123')).toBe(false)

    // Too long
    expect(isValidExternalId('col_01234567890abcdefghjkmnpqrs')).toBe(false)

    // Wrong separator
    expect(isValidExternalId('col-01234567890abcdefghjkmnpqr')).toBe(false)

    // Contains invalid Crockford characters (I, L, O, U)
    expect(isValidExternalId('col_IIIIIIIIIIIIIIIIIIIIIIIIII')).toBe(false)
    expect(isValidExternalId('col_LLLLLLLLLLLLLLLLLLLLLLLLLL')).toBe(false)
    expect(isValidExternalId('col_OOOOOOOOOOOOOOOOOOOOOOOOOO')).toBe(false)
    expect(isValidExternalId('col_UUUUUUUUUUUUUUUUUUUUUUUUUU')).toBe(false)
  })
})

describe('getEntityType', () => {
  test('returns entity type for valid external IDs', () => {
    expect(getEntityType('col_01234567890abcdefghjkmnpqr')).toBe('Collection')
    expect(getEntityType('con_01234567890abcdefghjkmnpqr')).toBe('Connector')
    expect(getEntityType('pip_01234567890abcdefghjkmnpqr')).toBe('Pipeline')
    expect(getEntityType('res_01234567890abcdefghjkmnpqr')).toBe('AnalysisResult')
  })

  test('returns null for invalid external IDs', () => {
    expect(getEntityType('')).toBe(null)
    expect(getEntityType('xy')).toBe(null)
    expect(getEntityType('xyz_123')).toBe(null)
    expect(getEntityType('invalid')).toBe(null)
  })
})

describe('getPrefix', () => {
  test('returns prefix for valid external IDs', () => {
    expect(getPrefix('col_01234567890abcdefghjkmnpqr')).toBe('col')
    expect(getPrefix('con_01234567890abcdefghjkmnpqr')).toBe('con')
    expect(getPrefix('pip_01234567890abcdefghjkmnpqr')).toBe('pip')
    expect(getPrefix('res_01234567890abcdefghjkmnpqr')).toBe('res')
  })

  test('returns null for invalid external IDs', () => {
    expect(getPrefix('')).toBe(null)
    expect(getPrefix('invalid')).toBe(null)
    expect(getPrefix('123')).toBe(null)
  })
})

describe('isNumericId', () => {
  test('identifies numeric IDs', () => {
    expect(isNumericId('123')).toBe(true)
    expect(isNumericId('0')).toBe(true)
    expect(isNumericId('999999')).toBe(true)
  })

  test('rejects non-numeric strings', () => {
    expect(isNumericId('')).toBe(false)
    expect(isNumericId('abc')).toBe(false)
    expect(isNumericId('col_123')).toBe(false)
    expect(isNumericId('12.34')).toBe(false)
    expect(isNumericId('-123')).toBe(false)
    expect(isNumericId(null as any)).toBe(false)
  })
})

describe('isExternalId', () => {
  test('identifies external IDs', () => {
    expect(isExternalId('col_01234567890abcdefghjkmnpqr')).toBe(true)
    expect(isExternalId('con_01234567890abcdefghjkmnpqr')).toBe(true)
  })

  test('rejects non-external IDs', () => {
    expect(isExternalId('123')).toBe(false)
    expect(isExternalId('invalid')).toBe(false)
    expect(isExternalId('')).toBe(false)
  })
})

describe('getIdentifierType', () => {
  test('identifies numeric type', () => {
    expect(getIdentifierType('123')).toBe('numeric')
    expect(getIdentifierType('999')).toBe('numeric')
  })

  test('identifies external type', () => {
    expect(getIdentifierType('col_01234567890abcdefghjkmnpqr')).toBe('external')
    expect(getIdentifierType('con_01234567890abcdefghjkmnpqr')).toBe('external')
  })

  test('identifies invalid type', () => {
    expect(getIdentifierType('')).toBe('invalid')
    expect(getIdentifierType('invalid')).toBe('invalid')
    expect(getIdentifierType('col_123')).toBe('invalid')
  })
})

describe('formatExternalId', () => {
  test('formats with prefix', () => {
    const result = formatExternalId('col_01234567890abcdefghjkmnpqr')
    expect(result).toBe('col_01234567...')
  })

  test('formats without prefix', () => {
    const result = formatExternalId('col_01234567890abcdefghjkmnpqr', false)
    expect(result).toBe('01234567...')
  })

  test('returns original for invalid ID', () => {
    expect(formatExternalId('invalid')).toBe('invalid')
    expect(formatExternalId('')).toBe('')
  })
})

describe('copyExternalId', () => {
  test('copies to clipboard using Clipboard API', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.assign(navigator, {
      clipboard: { writeText: writeTextMock },
    })

    await copyExternalId('col_01234567890abcdefghjkmnpqr')

    expect(writeTextMock).toHaveBeenCalledWith('col_01234567890abcdefghjkmnpqr')
  })
})

describe('ENTITY_PREFIXES', () => {
  test('contains all entity types', () => {
    expect(ENTITY_PREFIXES.col).toBe('Collection')
    expect(ENTITY_PREFIXES.con).toBe('Connector')
    expect(ENTITY_PREFIXES.pip).toBe('Pipeline')
    expect(ENTITY_PREFIXES.res).toBe('AnalysisResult')
  })
})
