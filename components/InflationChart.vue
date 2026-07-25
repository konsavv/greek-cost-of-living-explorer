<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Filler
} from 'chart.js'

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Filler)

const props = defineProps<{ inflation: { year: number; hicp: number }[] }>()

const chartData = computed(() => ({
  labels: props.inflation.map((d) => d.year),
  datasets: [
    {
      label: 'HICP annual inflation (%)',
      data: props.inflation.map((d) => d.hicp),
      borderColor: '#2a78d6',
      backgroundColor: 'rgba(42, 120, 214, 0.10)',
      borderWidth: 2,
      pointRadius: 3,
      pointBackgroundColor: '#2a78d6',
      tension: 0.25,
      fill: true
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: { label: (ctx: any) => ` ${ctx.parsed.y}%` }
    }
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#898781' },
      border: { color: '#c3c2b7' }
    },
    y: {
      ticks: { callback: (v: any) => v + '%', color: '#898781' },
      grid: { color: '#e1e0d9' },
      border: { display: false }
    }
  }
}
</script>

<template>
  <div class="chart-box">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
