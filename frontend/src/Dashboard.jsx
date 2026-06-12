import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tenantId] = useState(localStorage.getItem('tenantId') || 'default');

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/dashboard/overview`, {
        headers: {
          'X-Tenant-ID': tenantId,
          'X-User-ID': 'user_123'
        }
      });
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8">Loading...</div>;

  const kpis = metrics?.kpis || {};

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">RAG Platform Dashboard</h1>
          <p className="text-gray-600">Enterprise observability and metrics</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <KPICard title="Total Queries" value={kpis.total_queries} />
          <KPICard title="Avg Latency" value={`${kpis.avg_latency_ms}ms`} />
          <KPICard title="Total Cost" value={`$${kpis.total_cost_usd}`} />
          <KPICard title="Hallucination Rate" value={`${(kpis.hallucination_rate * 100).toFixed(1)}%`} />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Latency Trend */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Response Latency Trend</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={[
                { time: '12:00', latency: 3200 },
                { time: '13:00', latency: 3400 },
                { time: '14:00', latency: 3100 },
                { time: '15:00', latency: 3600 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="latency" stroke="#3b82f6" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Cost Breakdown */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Cost by Model</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { model: 'GPT-4 Turbo', cost: 98.32 },
                { model: 'Cross-Encoder', cost: 50.20 },
                { model: 'Embeddings', cost: 15.00 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="model" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="cost" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Quality Metrics */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">RAG Quality Metrics</h2>
            <div className="space-y-4">
              <MetricBar label="Context Precision" value={kpis.avg_context_precision} />
              <MetricBar label="Context Recall" value={kpis.avg_context_recall} />
              <MetricBar label="Faithfulness" value={1 - kpis.hallucination_rate} />
            </div>
          </div>

          {/* A/B Test Results */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">A/B Test Results</h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="font-medium">Variant A: 512 tokens</span>
                <span className="text-green-600">↑ Winning</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '65%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({ title, value }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <p className="text-gray-600 text-sm font-medium">{title}</p>
      <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
    </div>
  );
}

function MetricBar({ label, value }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-medium text-gray-900">{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-500 h-2 rounded-full" 
          style={{ width: `${value * 100}%` }}
        ></div>
      </div>
    </div>
  );
}
