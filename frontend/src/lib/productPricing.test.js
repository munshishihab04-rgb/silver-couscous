import { productPrice } from "./productPricing";


test("returns null when no seller-authoritative variant price exists", () => {
  expect(productPrice({ variants: [{ price_eur: null }] })).toBeNull();
});


test("returns the lowest positive variant price", () => {
  expect(productPrice({ variants: [{ price_eur: 29.9 }, { price_eur: 19.9 }] })).toBe(19.9);
});
