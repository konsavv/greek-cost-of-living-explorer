// Loads the dataset produced by the Python ETL (public/data/economy.json).
// useFetch caches on the payload key, so SSR + client share one request.
export interface Region {
  region: string
  code: string
  income_year_eur: number      // disposable income per inhabitant, annual
  income_month_eur: number     // same, divided by 12
  income_is_real: boolean      // true when Eurostat live data was used
  income_year_ref: number | null
  rent_1br_eur: number
  rent_2br_eur: number
  affordability_pct: number    // 1BR rent as % of monthly income per inhabitant
}

export interface Economy {
  meta: {
    generated_at: string
    inflation_source: string
    income_source: string
    income_real_count: number
    rent_source: string
    note: string
  }
  regions: Region[]
  inflation: { year: number; hicp: number }[]
}

export function useEconomy() {
  // Load client-side: economy.json is a static file in public/, and Nuxt's dev
  // server does not serve public assets during server-side rendering, which made
  // the SSR fetch fail. Fetching in the browser works in both dev and production.
  return useFetch<Economy>('/data/economy.json', {
    key: 'economy',
    server: false,
    default: () => null
  })
}

// Affordability status buckets. ~30% on rent is the common benchmark.
export function affordabilityStatus(pct: number): 'good' | 'warning' | 'critical' {
  if (pct < 33) return 'good'
  if (pct <= 40) return 'warning'
  return 'critical'
}

export function euro(n: number): string {
  return '€' + n.toLocaleString('en-US')
}
