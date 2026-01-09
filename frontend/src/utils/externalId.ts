/**
 * External ID utilities for entity identification.
 *
 * Provides validation and parsing functions for external IDs
 * in the format {prefix}_{base32_uuid}.
 *
 * External ID Format:
 *   - prefix: 3-character entity type identifier
 *   - separator: underscore (_)
 *   - uuid: 26-character Crockford Base32 encoded UUIDv7
 *
 * Entity Prefixes:
 *   - col: Collection
 *   - con: Connector
 *   - pip: Pipeline
 *   - res: AnalysisResult
 */

/**
 * Entity type prefixes
 */
export type EntityPrefix = 'col' | 'con' | 'pip' | 'res'

/**
 * Entity type names mapped to prefixes
 */
export const ENTITY_PREFIXES: Record<EntityPrefix, string> = {
  col: 'Collection',
  con: 'Connector',
  pip: 'Pipeline',
  res: 'AnalysisResult',
}

/**
 * Crockford Base32 alphabet (excludes I, L, O, U to avoid confusion)
 */
const CROCKFORD_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'

/**
 * Regex pattern for validating external IDs
 * Format: {3-char prefix}_{26-char Crockford Base32}
 */
const EXTERNAL_ID_PATTERN = /^(col|con|pip|res)_[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$/i

/**
 * Validates if a string is a valid external ID.
 *
 * @param id - The string to validate
 * @param expectedPrefix - Optional prefix to validate against
 * @returns True if valid external ID format
 *
 * @example
 * isValidExternalId('col_01hgw2bbg0000000000000000') // true
 * isValidExternalId('col_01hgw2bbg0000000000000000', 'col') // true
 * isValidExternalId('col_01hgw2bbg0000000000000000', 'con') // false
 */
export function isValidExternalId(id: string, expectedPrefix?: EntityPrefix): boolean {
  if (!id || typeof id !== 'string') {
    return false
  }

  if (!EXTERNAL_ID_PATTERN.test(id)) {
    return false
  }

  if (expectedPrefix) {
    const prefix = id.slice(0, 3).toLowerCase() as EntityPrefix
    return prefix === expectedPrefix
  }

  return true
}

/**
 * Extracts the entity type from an external ID.
 *
 * @param externalId - The external ID string
 * @returns The entity type name, or null if invalid
 *
 * @example
 * getEntityType('col_01hgw2bbg0000000000000000') // 'Collection'
 * getEntityType('con_01hgw2bbg0000000000000001') // 'Connector'
 * getEntityType('invalid') // null
 */
export function getEntityType(externalId: string): string | null {
  if (!externalId || externalId.length < 3) {
    return null
  }

  const prefix = externalId.slice(0, 3).toLowerCase() as EntityPrefix
  return ENTITY_PREFIXES[prefix] || null
}

/**
 * Extracts the prefix from an external ID.
 *
 * @param externalId - The external ID string
 * @returns The prefix, or null if invalid
 *
 * @example
 * getPrefix('col_01hgw2bbg0000000000000000') // 'col'
 * getPrefix('invalid') // null
 */
export function getPrefix(externalId: string): EntityPrefix | null {
  if (!isValidExternalId(externalId)) {
    return null
  }

  return externalId.slice(0, 3).toLowerCase() as EntityPrefix
}

/**
 * Checks if a string is a numeric ID (for backward compatibility).
 *
 * @param id - The string to check
 * @returns True if the string is numeric
 *
 * @example
 * isNumericId('123') // true
 * isNumericId('col_xxx') // false
 */
export function isNumericId(id: string): boolean {
  if (!id || typeof id !== 'string') {
    return false
  }

  return /^\d+$/.test(id)
}

/**
 * Checks if a string is an external ID.
 *
 * @param id - The string to check
 * @returns True if the string matches external ID format
 *
 * @example
 * isExternalId('col_01hgw2bbg0000000000000000') // true
 * isExternalId('123') // false
 */
export function isExternalId(id: string): boolean {
  return isValidExternalId(id)
}

/**
 * Determines the identifier type (numeric or external).
 *
 * @param id - The identifier string
 * @returns 'numeric' | 'external' | 'invalid'
 *
 * @example
 * getIdentifierType('123') // 'numeric'
 * getIdentifierType('col_xxx') // 'external'
 * getIdentifierType('invalid') // 'invalid'
 */
export function getIdentifierType(id: string): 'numeric' | 'external' | 'invalid' {
  if (isNumericId(id)) {
    return 'numeric'
  }

  if (isExternalId(id)) {
    return 'external'
  }

  return 'invalid'
}

/**
 * Formats an external ID for display (truncated with ellipsis).
 *
 * @param externalId - The external ID string
 * @param showPrefix - Whether to include the prefix (default: true)
 * @returns Formatted string for display
 *
 * @example
 * formatExternalId('col_01hgw2bbg0000000000000000') // 'col_01hgw2bb...'
 * formatExternalId('col_01hgw2bbg0000000000000000', false) // '01hgw2bb...'
 */
export function formatExternalId(externalId: string, showPrefix = true): string {
  if (!isValidExternalId(externalId)) {
    return externalId
  }

  if (showPrefix) {
    // Show prefix + first 8 chars of base32 + ellipsis
    return externalId.slice(0, 12) + '...'
  }

  // Show first 8 chars of base32 + ellipsis
  return externalId.slice(4, 12) + '...'
}

/**
 * Copies an external ID to the clipboard.
 *
 * @param externalId - The external ID to copy
 * @returns Promise that resolves when copied
 */
export async function copyExternalId(externalId: string): Promise<void> {
  if (typeof navigator?.clipboard?.writeText === 'function') {
    await navigator.clipboard.writeText(externalId)
  } else {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = externalId
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  }
}
