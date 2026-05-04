// components/agent/AnalyticsCharts.tsx
// --------------------------------------
// Renders bar charts returned by the analytics agent.
// Uses recharts (already in most React project deps).
//
// If recharts is not installed: npm install recharts
//
// Each chart in the "charts" array from ui_hints is rendered as
// a separate ResponsiveContainer + BarChart block.

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ChartData } from '../../types/agent';

interface Props {
  charts: ChartData[];
}

// Colour palette for bar fills — cycles if more bars than colours
const BAR_COLOURS = [
  '#6C63FF', '#48C78E', '#F97316', '#3B82F6', '#EC4899', '#14B8A6',
];

const AnalyticsCharts: React.FC<Props> = ({ charts }) => (
  <div className="analytics-charts">
    {charts.map((chart) => (
      <div key={chart.title} className="chart-block">
        <p className="chart-title">{chart.title}</p>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart
            data={chart.data}
            margin={{ top: 4, right: 8, left: -16, bottom: 4 }}
          >
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
              cursor={{ fill: 'rgba(0,0,0,0.05)' }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chart.data.map((_, idx) => (
                <Cell
                  key={idx}
                  fill={BAR_COLOURS[idx % BAR_COLOURS.length]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    ))}
  </div>
);

export default AnalyticsCharts;
