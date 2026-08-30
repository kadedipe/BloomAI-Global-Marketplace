import {describe, expect, it} from 'vitest';
import {isSupportedProductImage, normalizePredictions, readError} from './utils.js';

describe('marketplace UI contracts', () => {
  it('normalizes five ranked AI predictions', () => {
    const predictions = Array.from({length: 7}, (_, index) => ({name: `flower-${index}`, confidence: index / 10}));
    expect(normalizePredictions(predictions)).toHaveLength(5);
    expect(normalizePredictions(predictions)[0].confidence).toBe(0.6);
  });

  it('formats FastAPI validation errors', async () => {
    const response = {json: async () => ({detail: [{msg: 'Required'}, {msg: 'Invalid'}]})};
    await expect(readError(response, 'Fallback')).resolves.toBe('Required. Invalid');
  });

  it('accepts only supported product image MIME types', () => {
    expect(isSupportedProductImage({type: 'image/webp'})).toBe(true);
    expect(isSupportedProductImage({type: 'image/svg+xml'})).toBe(false);
  });
});
