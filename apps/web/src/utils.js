export async function readError(response, fallback) {
  try {
    const body = await response.json();
    if (Array.isArray(body.detail)) return body.detail.map(item => item.msg).join('. ');
    return body.detail || fallback;
  } catch {
    return fallback;
  }
}

export function normalizePredictions(predictions) {
  if (!Array.isArray(predictions)) return [];
  return predictions
    .filter(item => item && Number.isFinite(Number(item.confidence)))
    .sort((left, right) => Number(right.confidence) - Number(left.confidence))
    .slice(0, 5);
}

export function isSupportedProductImage(file) {
  return Boolean(file && ['image/jpeg', 'image/png', 'image/webp'].includes(file.type));
}
