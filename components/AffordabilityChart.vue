<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip
} from 'chart.js'
import type { Region } from '~/composables/useEconomy'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip)

const props = defineProps<{ regions: Region[]; selected: string }>()

// Sorted most-affordable first (data is already sorted, but be defensive).
const sorted = computed(() =>
  [...props.regions].sort((a, b) => a.affordability_pct - b.affordability_pct)
)

const chartData = computed(() => ({
  labels: sorted.value.map((r) => r.region),
  datasets: [
    {
      label: 'Rent as % of net salary',
      data: sorted.value.map((r) => r.affordability_pct),
      // Color follows the entity: the selected region is highlighted in orange,
      // every other bar shares the single blue series colour.
      backgroundColor: sorted.value.map((r) =>
        r.region === props.selected ? '#eb6834' : '#2a78d6'
      ),
      borderRadius: 4,
      borderSkipped: false,
      barThickness: 16
    }
  ]
}))

const chartOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => ` ${ctx.parsed.x}% of monthly income on rent`
      }
    }
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: { callback: (v: any) => v + '%', color: '#898781' },
      grid: { color: '#e1e0d9' },
      border: { display: false }
    },
    y: {
      ticks: { color: '#52514e', font: { size: 11 } },
      grid: { display: false },
      border: { display: false }
    }
  }
}
</script>

<template>
  <div class="chart-box">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
