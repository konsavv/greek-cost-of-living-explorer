<script setup lang="ts">
import { affordabilityStatus, euro, type Region } from '~/composables/useEconomy'

defineProps<{ regions: Region[]; selected: string }>()

const statusLabel: Record<string, string> = {
  good: 'Affordable',
  warning: 'Stretched',
  critical: 'Unaffordable'
}
</script>

<template>
  <div class="panel">
    <h2>All regions</h2>
    <p class="sub">
      Sorted by affordability. Income is real Eurostat/ELSTAT data; rent is indicative
      market data — see the note below.
    </p>
    <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th>Region</th>
            <th>Income/capita (mo)</th>
            <th>Rent 1BR</th>
            <th>Rent 2BR</th>
            <th>Rent / income</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in regions"
            :key="r.code"
            :class="{ selected: r.region === selected }"
          >
            <td>{{ r.region }}</td>
            <td>{{ euro(r.income_month_eur) }}</td>
            <td>{{ euro(r.rent_1br_eur) }}</td>
            <td>{{ euro(r.rent_2br_eur) }}</td>
            <td>{{ r.affordability_pct }}%</td>
            <td>
              <span class="pill" :class="affordabilityStatus(r.affordability_pct)">
                {{ statusLabel[affordabilityStatus(r.affordability_pct)] }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
