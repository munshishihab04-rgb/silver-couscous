export function productPrice(product) {
  const prices = (product?.variants || [])
    .map((variant) => variant?.price_eur)
    .filter((price) => Number.isFinite(price) && price > 0);
  return prices.length ? Math.min(...prices) : null;
}
