import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Activity, BarChart3, Cloud, Droplets, Moon, Play, RefreshCcw, Satellite, Sprout, Sun, Waves } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { compareNoise, generateSeason } from './api';
import type { ComparePayload, CropName, MatrixPayload, ModelMetrics, Observation, SeasonPayload, SeasonRequest } from './types';

const crops: CropName[] = ['All', 'Rice', 'Wheat', 'Cotton', 'Sugarcane'];
const tabs = ['Dashboard', 'Simulator', 'Classification', 'Growth Stage', 'Analytics', 'Water Advisory', 'Settings'];
const palette = ['#2f9e44', '#1c7ed6', '#f08c00', '#9c36b5', '#0ca678', '#e03131'];
const initialConfig: SeasonRequest = { crop: 'All', planting_date: '2026-06-15', plots_per_crop: 8, cloud_percent: 18, noise_level: 0.025, revisit_days: 5, seed: null };

function pct(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '0.0%';
  return `${(value * 100).toFixed(1)}%`;
}

function avg(values: number[]) {
  return values.length ? Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(3)) : null;
}

function aggregateTimeline(data: Observation[], crop: CropName) {
  const filtered = crop === 'All' ? data : data.filter((row) => row.crop === crop);
  const buckets = new Map<number, { day: number; ndvi: number[]; ndmi: number[]; stress: number[]; trueNdvi: number[] }>();
  filtered.forEach((row) => {
    const day = Math.round(row.day_norm * 100);
    const bucket = buckets.get(day) || { day, ndvi: [], ndmi: [], stress: [], trueNdvi: [] };
    if (row.observed_ndvi !== null) bucket.ndvi.push(row.observed_ndvi);
    if (row.observed_ndmi !== null) bucket.ndmi.push(row.observed_ndmi);
    bucket.stress.push(row.stress_score);
    bucket.trueNdvi.push(row.true_ndvi);
    buckets.set(day, bucket);
  });
  return Array.from(buckets.values()).sort((a, b) => a.day - b.day).map((b) => ({
    day: b.day,
    NDVI: avg(b.ndvi),
    NDMI: avg(b.ndmi),
    Stress: avg(b.stress),
    TrueNDVI: avg(b.trueNdvi),
  }));
}

function Card({ title, value, icon, sub }: { title: string; value: string; icon: ReactNode; sub?: string }) {
  return (
    <section className="metric-card">
      <div className="metric-icon">{icon}</div>
      <p>{title}</p>
      <strong>{value}</strong>
      {sub && <span>{sub}</span>}
    </section>
  );
}

function Timeline({ data, keys }: { data: any[]; keys: string[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="day" />
        <YAxis domain={[0, 1]} />
        <Tooltip />
        {keys.map((key, i) => <Line key={key} type="monotone" dataKey={key} stroke={palette[i]} strokeWidth={2.5} dot={false} connectNulls />)}
      </LineChart>
    </ResponsiveContainer>
  );
}

function Matrix({ matrix }: { matrix: MatrixPayload }) {
  if (!matrix.matrix.length) return <div className="empty">Not enough clear observations.</div>;
  const max = Math.max(...matrix.matrix.flat(), 1);
  return (
    <div className="matrix" style={{ gridTemplateColumns: `120px repeat(${matrix.labels.length}, minmax(58px, 1fr))` }}>
      <div />
      {matrix.labels.map((label) => <b key={label}>{label}</b>)}
      {matrix.matrix.map((row, i) => [
        <b key={`r-${matrix.labels[i]}`}>{matrix.labels[i]}</b>,
        ...row.map((value, j) => <span key={`${i}-${j}`} style={{ background: `rgba(47,158,68,${0.12 + (value / max) * 0.78})` }}>{value}</span>),
      ])}
    </div>
  );
}

function Report({ metrics }: { metrics: ModelMetrics }) {
  const rows = Object.entries(metrics.classification_report || {}).filter(([key]) => metrics.labels?.includes(key));
  return <div className="report">{rows.map(([label, value]: any) => <div key={label}><b>{label}</b><span>Precision {pct(value.precision)}</span><span>Recall {pct(value.recall)}</span><span>F1 {pct(value['f1-score'])}</span></div>)}</div>;
}

function PieBlock({ data }: { data: { name: string; value: number }[] }) {
  return <ResponsiveContainer width="100%" height={280}><PieChart><Pie data={data} dataKey="value" nameKey="name" outerRadius={95} label>{data.map((_, i) => <Cell key={i} fill={palette[i % palette.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer>;
}

function Controls({ config, setConfig, runGenerate, busy }: { config: SeasonRequest; setConfig: any; runGenerate: any; busy: boolean }) {
  const update = (patch: Partial<SeasonRequest>) => setConfig((old: SeasonRequest) => ({ ...old, ...patch }));
  return (
    <div className="control-grid">
      <label>Crop<select value={config.crop} onChange={(e) => update({ crop: e.target.value as CropName })}>{crops.map((crop) => <option key={crop}>{crop}</option>)}</select></label>
      <label>Planting Date<input type="date" value={config.planting_date} onChange={(e) => update({ planting_date: e.target.value })} /></label>
      <label>Cloud %<input type="range" min="0" max="85" value={config.cloud_percent} onChange={(e) => update({ cloud_percent: Number(e.target.value) })} /><span>{config.cloud_percent}%</span></label>
      <label>Noise<input type="range" min="0" max="0.18" step="0.005" value={config.noise_level} onChange={(e) => update({ noise_level: Number(e.target.value) })} /><span>{config.noise_level.toFixed(3)}</span></label>
      <label>Revisit Days<input type="number" min="1" max="16" value={config.revisit_days} onChange={(e) => update({ revisit_days: Number(e.target.value) })} /></label>
      <label>Plots / Crop<input type="number" min="2" max="40" value={config.plots_per_crop} onChange={(e) => update({ plots_per_crop: Number(e.target.value) })} /></label>
      <button onClick={() => runGenerate({ ...config, cloud_percent: Math.min(85, config.cloud_percent + 15) })} disabled={busy}><Cloud />Increase Cloud</button>
      <button onClick={() => runGenerate({ ...config, noise_level: Math.min(0.18, config.noise_level + 0.025) })} disabled={busy}><Activity />Increase Noise</button>
    </div>
  );
}

function CompareBlock({ compare }: { compare: ComparePayload }) {
  const data = [
    { name: 'Low crop', accuracy: compare.low_noise.metrics.crop_classifier.accuracy },
    { name: 'High crop', accuracy: compare.high_noise.metrics.crop_classifier.accuracy },
    { name: 'Low stage', accuracy: compare.low_noise.metrics.growth_stage_predictor.accuracy },
    { name: 'High stage', accuracy: compare.high_noise.metrics.growth_stage_predictor.accuracy },
  ];
  return <div><p className="readable">{compare.interpretation}</p><ResponsiveContainer width="100%" height={260}><BarChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis domain={[0, 1]} /><Tooltip /><Bar dataKey="accuracy" fill="#1c7ed6" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer><div className="delta">Accuracy delta: crop {pct(compare.accuracy_delta.crop_classifier)}, stage {pct(compare.accuracy_delta.growth_stage_predictor)}</div></div>;
}

function Advice({ row }: { row: Observation }) {
  return <div className="advice"><strong>{row.advisory?.level || row.water_stress_label}</strong><p>{row.advisory?.reason || `${row.crop} ${row.stage_name}`}</p><p>{row.advisory?.recommendation}</p><div><span>Crop {row.crop}</span><span>Stage {row.stage_name}</span><span>NDVI {row.observed_ndvi?.toFixed(3)}</span><span>NDMI {row.observed_ndmi?.toFixed(3)}</span><span>Stress {row.stress_score.toFixed(2)}</span></div></div>;
}

export default function App() {
  const [tab, setTab] = useState('Dashboard');
  const [config, setConfig] = useState<SeasonRequest>(initialConfig);
  const [season, setSeason] = useState<SeasonPayload | null>(null);
  const [compare, setCompare] = useState<ComparePayload | null>(null);
  const [selectedCrop, setSelectedCrop] = useState<CropName>('All');
  const [selectedPlot, setSelectedPlot] = useState('');
  const [dark, setDark] = useState(true);
  const [frame, setFrame] = useState(60);
  const [busy, setBusy] = useState(false);

  async function runGenerate(nextConfig = config) {
    setBusy(true);
    try {
      const payload = await generateSeason(nextConfig);
      setSeason(payload);
      setSelectedPlot(payload.summary.latest_plot_status[0]?.plot_id || '');
      setSelectedCrop(nextConfig.crop);
      setCompare(null);
    } finally {
      setBusy(false);
    }
  }

  async function runCompare() {
    setBusy(true);
    try {
      setCompare(await compareNoise(config));
      setTab('Analytics');
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    runGenerate(initialConfig);
  }, []);

  const timeline = useMemo(() => aggregateTimeline(season?.observations || [], selectedCrop), [season, selectedCrop]);
  const clearRows = useMemo(() => (season?.summary.latest_plot_status || []).filter((row) => row.observed_ndvi !== null), [season]);
  const plotOptions = useMemo(() => Array.from(new Set((season?.observations || []).map((row) => row.plot_id))).slice(0, 40), [season]);
  const plotTimeline = useMemo(() => (season?.observations || []).filter((row) => row.plot_id === selectedPlot && row.day_norm * 100 <= frame).map((row) => ({ day: row.day, NDVI: row.observed_ndvi, NDMI: row.observed_ndmi, Stress: row.stress_score })), [season, selectedPlot, frame]);
  const latest = clearRows.find((row) => row.plot_id === selectedPlot) || clearRows[0];
  const cropPie = Object.entries(season?.summary.crop_counts || {}).map(([name, value]) => ({ name, value }));
  const stressPie = Object.entries(season?.summary.stress_counts || {}).map(([name, value]) => ({ name, value }));

  return (
    <main className={dark ? 'app dark' : 'app'}>
      <aside className="sidebar">
        <div className="brand"><Satellite /><span>Crop Intel</span></div>
        {tabs.map((item) => <button className={tab === item ? 'active' : ''} key={item} onClick={() => setTab(item)}>{item}</button>)}
        <button className="theme" onClick={() => setDark(!dark)}>{dark ? <Sun /> : <Moon />}</button>
      </aside>

      <section className="content">
        <header className="topbar">
          <div><h1>Smart Satellite Crop Intelligence</h1><p>Fully synthetic crop, growth stage, and water-deficit intelligence.</p></div>
          <div className="actions">
            <button onClick={() => runGenerate({ ...config, seed: Math.floor(Math.random() * 1_000_000_000) })} disabled={busy}><RefreshCcw />New Seed</button>
            <button onClick={() => runGenerate()} disabled={busy}><Play />Generate Season</button>
          </div>
        </header>
        <div className="disclosure">Every row is synthetic and generated by this simulator. Clean true values are shown for transparency only and are excluded from ML features.</div>

        {tab === 'Dashboard' && season && <div className="stack"><div className="cards"><Card title="Crop Classifier" value={pct(season.metrics.crop_classifier.accuracy)} icon={<Sprout />} sub="Random Forest" /><Card title="Stage Predictor" value={pct(season.metrics.growth_stage_predictor.accuracy)} icon={<Activity />} sub="Observed features only" /><Card title="Mean NDVI" value={String(season.summary.mean_observed_ndvi ?? 'n/a')} icon={<BarChart3 />} sub="Clear observations" /><Card title="Mean NDMI" value={String(season.summary.mean_observed_ndmi ?? 'n/a')} icon={<Droplets />} sub="Canopy moisture" /><Card title="Cloud Realized" value={`${season.summary.cloud_percent_realized}%`} icon={<Cloud />} sub={`${season.summary.missing_observations} missing rows`} /></div><div className="grid two"><section className="panel"><h2>NDVI Timeline</h2><Timeline data={timeline} keys={['NDVI', 'TrueNDVI']} /></section><section className="panel"><h2>NDMI and Stress</h2><Timeline data={timeline} keys={['NDMI', 'Stress']} /></section></div></div>}

        {tab === 'Simulator' && <div className="grid two"><section className="panel"><h2>Season Controls</h2><Controls config={config} setConfig={setConfig} runGenerate={runGenerate} busy={busy} /></section><section className="panel"><h2>Season Animation</h2><div className="inline"><select value={selectedPlot} onChange={(e) => setSelectedPlot(e.target.value)}>{plotOptions.map((plot) => <option key={plot}>{plot}</option>)}</select><input type="range" min="0" max="100" value={frame} onChange={(e) => setFrame(Number(e.target.value))} /></div><Timeline data={plotTimeline} keys={['NDVI', 'NDMI', 'Stress']} /></section></div>}

        {tab === 'Classification' && season && <div className="grid two"><section className="panel"><h2>Crop Confusion Matrix</h2><Matrix matrix={season.metrics.crop_classifier.confusion_matrix} /></section><section className="panel"><h2>Precision / Recall / F1</h2><Report metrics={season.metrics.crop_classifier} /></section></div>}
        {tab === 'Growth Stage' && season && <div className="grid two"><section className="panel"><h2>Stage Confusion Matrix</h2><Matrix matrix={season.metrics.growth_stage_predictor.confusion_matrix} /></section><section className="panel"><h2>Growth Curve</h2><Timeline data={timeline} keys={['NDVI', 'NDMI']} /></section></div>}

        {tab === 'Analytics' && season && <div className="stack"><div className="grid two"><section className="panel"><h2>Crop Mix</h2><PieBlock data={cropPie} /></section><section className="panel"><h2>Stress Labels</h2><PieBlock data={stressPie} /></section></div><section className="panel"><h2>Before / After Noise</h2><button onClick={runCompare} disabled={busy}><Waves />Compare Before After</button>{compare && <CompareBlock compare={compare} />}</section></div>}
        {tab === 'Water Advisory' && <div className="grid two"><section className="panel"><h2>Current Recommendation</h2>{latest && <Advice row={latest} />}</section><section className="panel"><h2>Plot Status</h2><div className="table">{clearRows.slice(0, 16).map((row) => <button key={row.plot_id} onClick={() => setSelectedPlot(row.plot_id)}><span>{row.plot_id}</span><b>{row.crop}</b><em>{row.water_stress_label}</em></button>)}</div></section></div>}
        {tab === 'Settings' && <section className="panel"><h2>Research-grounded Simulator Parameters</h2><p className="readable">Crop calendars and water ranges are based on FAO tables. NDVI rises with canopy density and declines near maturity. NDMI follows canopy moisture and drops faster during stress. Sentinel-like revisit and cloud contamination create the observations used by ML.</p><Controls config={config} setConfig={setConfig} runGenerate={runGenerate} busy={busy} /></section>}
      </section>
    </main>
  );
}
