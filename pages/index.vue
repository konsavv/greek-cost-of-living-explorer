<script setup lang="ts">
import { affordabilityStatus, euro } from '~/composables/useEconomy'

const { data: economy, pending, error } = useEconomy()

// --- filter state ---
const selected = ref('Attica (Athens)')

// Keep the default valid once data arrives.
watch(economy, (e) => {
  if (e && !e.regions.some((r) => r.region === selected.value)) {
    selected.value = e.regions[0]?.region ?? ''
  }
})

const selectedRegion = computed(() =>
  economy.value?.regions.find((r) => r.region === selected.value)
)

const avgRent1br = computed(() => {
  const rs = economy.value?.regions ?? []
  if (!rs.length) return 0
  return Math.round(rs.reduce((s, r) => s + r.rent_1br_eur, 0) / rs.length)
})

const latestInflation = computed(() => {
  const inf = economy.value?.inflation ?? []
  return inf.length ? inf[inf.length - 1] : null
})
</script>

<template>
  <div class="wrap">
    <header class="hero">
      <h1>Greek Cost-of-Living &amp; Real Estate Explorer</h1>
      <p>
        Compare rent, salaries and affordability across Greek regions, and track
        national inflation. Built with a Python ETL pipeline and a Nuxt&nbsp;3 front-end.
      </p>
      <div v-if="economy" class="stamp">
        Data generated {{ new Date(economy.meta.generated_at).toLocaleDateString() }} ·
        Inflation: {{ economy.meta.inflation_source }} ·
        Income: {{ economy.meta.income_source }}
      </div>
    </header>

    <p v-if="pending">Loading data…</p>
    <p v-else-if="error">Could not load data. Run the ETL: <code>python etl/etl.py</code></p>

    <template v-else-if="economy">
      <!-- Filter -->
      <div class="filters">
        <label for="region">Region</label>
        <select id="region" v-model="selected">
          <option v-for="r in economy.regions" :key="r.code" :value="r.region">
            {{ r.region }}
          </option>
        </select>
      </div>

      <!-- KPI row -->
      <div class="kpi-row">
        <KpiCard
          label="Avg rent (1-bedroom)"
          :value="euro(avgRent1br)"
          hint="Across all regions"
        />
        <KpiCard
          v-if="selectedRegion"
          :label="`Income/capita — ${selectedRegion.region}`"
          :value="euro(selectedRegion.income_month_eur)"
          hint="Disposable income per inhabitant, monthly"
        />
        <KpiCard
          v-if="selectedRegion"
          label="Affordability"
          :value="`${selectedRegion.affordability_pct}%`"
          :accent="affordabilityStatus(selectedRegion.affordability_pct)"
          hint="1BR rent as share of monthly income"
        />
        <KpiCard
          v-if="latestInflation"
          :label="`Inflation ${latestInflation.year}`"
          :value="`${latestInflation.hicp}%`"
          hint="HICP, annual average"
        />
      </div>

      <!-- Charts -->
      <div class="grid-2">
        <div class="panel">
          <h2>Affordability by region</h2>
          <p class="sub">
            Rent (1BR) as % of monthly disposable income — lower is better. ≈30% is the
            common benchmark. Selected region highlighted.
          </p>
          <ClientOnly>
            <AffordabilityChart :regions="economy.regions" :selected="selected" />
          </ClientOnly>
        </div>
        <div class="panel">
          <h2>Inflation trend (Greece)</h2>
          <p class="sub">HICP annual average rate of change, {{ economy.inflation[0]?.year }}–{{ latestInflation?.year }}.</p>
          <ClientOnly>
            <InflationChart :inflation="economy.inflation" />
          </ClientOnly>
        </div>
      </div>

      <!-- Table -->
      <RegionsTable :regions="economy.regions" :selected="selected" />

      <footer class="note">
        <strong>About the data.</strong> Inflation (Eurostat <code>prc_hicp_aind</code>)
        and regional <strong>disposable income per inhabitant</strong> (Eurostat
        <code>tgs00026</code>, produced by
        <a href="https://www.statistics.gr/" target="_blank" rel="noopener">ELSTAT</a>)
        are fetched live by the ETL, with a bundled fallback when offline
        ({{ economy.meta.income_real_count }}/{{ economy.regions.length }} regions on
        live income this run). <strong>Rent figures are indicative market data</strong>
        (rent by region is not an official statistic) — replace them with a source you
        trust, e.g. Spitogatos / XE reports, in <code>etl/etl.py</code>.
      </footer>
    </template>
  </div>
</template>
