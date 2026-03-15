export function decimalToNumber(value: string | null | undefined): number {
  if (value === null || value === undefined) {
    return 0;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatCurrency(value: string | number, currencyCode = "EUR"): string {
  const amount = typeof value === "number" ? value : decimalToNumber(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(amount);
}

export function toIsoDate(input: Date): string {
  return input.toISOString().slice(0, 10);
}
