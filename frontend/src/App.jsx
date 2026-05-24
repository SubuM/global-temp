import React, { useState, useEffect, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Play, Pause, ArrowLeft, Globe, MapPin, Building } from 'lucide-react';

const MIN_YEAR = 1850;
const MAX_YEAR = 2013;

export default function App() {
    const [level, setLevel] = useState('global'); // global, country, city
    const [selectedCountry, setSelectedCountry] = useState(null);
    const [selectedCity, setSelectedCity] = useState(null);

    const [activeYear, setActiveYear] = useState(MIN_YEAR);
    const [isPlaying, setIsPlaying] = useState(true);

    const [dbStatus, setDbStatus] = useState({ connected: false, message: 'Checking...' });
    const [data, setData] = useState([]);
    const [dataSource, setDataSource] = useState('');

    // 1. Fetch System Status
    useEffect(() => {
        fetch('/api/status')
            .then(res => res.json())
            .then(res => setDbStatus({ connected: res.database_connected, message: res.message }))
            .catch(() => setDbStatus({ connected: false, message: 'API Offline' }));
    }, []);

    // 2. Fetch Data based on Level
    useEffect(() => {
        let url = '/api/temperatures/global';
        if (level === 'country') url = `/api/temperatures/country/${selectedCountry}`;
        if (level === 'city') url = `/api/temperatures/city/${selectedCountry}/${selectedCity}`;

        fetch(url)
            .then(res => res.json())
            .then(res => {
                setData(res.data);
                setDataSource(res.source);
            })
            .catch(err => console.error("Data fetch error:", err));
    }, [level, selectedCountry, selectedCity]);

    // 3. Animation Loop
    useEffect(() => {
        let interval;
        if (isPlaying) {
            interval = setInterval(() => {
                setActiveYear(prev => {
                    if (prev >= MAX_YEAR) return MIN_YEAR;
                    return prev + 1;
                });
            }, 150); // Animation speed
        }
        return () => clearInterval(interval);
    }, [isPlaying]);

    // 4. Data Processing for current year & trends
    const currentYearData = useMemo(() => data.filter(d => d.Year === activeYear), [data, activeYear]);

    const trendData = useMemo(() => {
        if (data.length === 0) return [];

        // Group by year to get averages
        const yearGroups = {};
        data.forEach(d => {
            if (!yearGroups[d.Year]) yearGroups[d.Year] = { Year: d.Year, total: 0, count: 0 };
            yearGroups[d.Year].total += d.AvgTemp;
            yearGroups[d.Year].count += 1;
        });

        const trend = Object.values(yearGroups)
            .map(g => ({ Year: g.Year, AvgTemp: g.total / g.count }))
            .sort((a, b) => a.Year - b.Year);

        // Calculate 10-year rolling average
        return trend.map((d, idx, arr) => {
            const window = arr.slice(Math.max(0, idx - 9), idx + 1);
            const rollAvg = window.reduce((sum, val) => sum + val.AvgTemp, 0) / window.length;
            return { ...d, RollingAvg: rollAvg };
        });
    }, [data]);

    const globalAvgTemp = currentYearData.length > 0
        ? (currentYearData.reduce((sum, d) => sum + d.AvgTemp, 0) / currentYearData.length).toFixed(2)
        : 0.0;

    // Render Helpers
    const handleMapClick = (e) => {
        if (!e || !e.points || e.points.length === 0) return;
        const point = e.points[0];

        if (level === 'global') {
            setSelectedCountry(point.location);
            setLevel('country');
            setActiveYear(MIN_YEAR);
        } else if (level === 'country') {
            setSelectedCity(point.hovertext);
            setLevel('city');
            setActiveYear(MIN_YEAR);
        }
    };

    return (
        <div className="min-h-screen flex font-sans">
            {/* Sidebar */}
            <aside className="w-72 bg-[#12121a] border-r border-white/10 p-6 flex flex-col gap-6">
                <div>
                    <h2 className="text-2xl font-display font-bold text-white mb-2">Global Temp Pulse</h2>
                    <p className="text-sm text-gray-400">Visualizing climate trends 1850 - 2013.</p>
                </div>

                <div className={`metric-card ${dbStatus.connected ? 'border-green-500' : 'border-orange-500'}`}>
                    <div className="text-xs text-gray-400 uppercase tracking-wide">Data Engine</div>
                    <div className="font-semibold text-white">{dbStatus.connected ? '🟢 SQL Server' : '🟡 Fallback Engine'}</div>
                </div>

                <div className="flex flex-col gap-3">
                    <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Navigation</h3>
                    {level !== 'global' && (
                        <button className="btn-primary" onClick={() => { setLevel('global'); setSelectedCountry(null); }}>
                            <Globe size={18} /> World View
                        </button>
                    )}
                    {level === 'city' && (
                        <button className="btn-primary" onClick={() => { setLevel('country'); setSelectedCity(null); }}>
                            <MapPin size={18} /> Country View
                        </button>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8 overflow-y-auto">
                {/* Breadcrumb */}
                <div className="text-gray-400 font-medium mb-6 flex gap-2 items-center">
                    <span className={level === 'global' ? 'text-primary' : ''}>🌍 Global</span>
                    {selectedCountry && <><span>&gt;</span><span className={level === 'country' ? 'text-primary' : ''}>📍 {selectedCountry}</span></>}
                    {selectedCity && <><span>&gt;</span><span className="text-primary">🏙️ {selectedCity}</span></>}
                </div>

                {/* Controls */}
                <div className="glass-card flex items-center gap-6">
                    <button className="btn-primary w-40" onClick={() => setIsPlaying(!isPlaying)}>
                        {isPlaying ? <><Pause size={18} /> Pause</> : <><Play size={18} /> Play</>}
                    </button>
                    <div className="flex-1 flex items-center gap-4">
                        <span className="text-gray-400 font-bold">{MIN_YEAR}</span>
                        <input
                            type="range"
                            min={MIN_YEAR} max={MAX_YEAR}
                            value={activeYear}
                            onChange={(e) => { setActiveYear(parseInt(e.target.value)); setIsPlaying(false); }}
                            className="w-full accent-primary cursor-pointer"
                        />
                        <span className="text-gray-400 font-bold">{MAX_YEAR}</span>
                    </div>
                </div>

                {/* Stats Row */}
                <div className="grid grid-cols-3 gap-6 mb-6">
                    <div className="metric-card border-primary">
                        <div className="text-xs text-gray-400 uppercase tracking-wide">Simulation Year</div>
                        <div className="text-3xl font-display font-bold text-white">{activeYear}</div>
                    </div>
                    <div className="metric-card border-cyan-500">
                        <div className="text-xs text-gray-400 uppercase tracking-wide">Avg Temp</div>
                        <div className="text-3xl font-display font-bold text-white">{globalAvgTemp} °C</div>
                    </div>
                    <div className="metric-card border-purple-500">
                        <div className="text-xs text-gray-400 uppercase tracking-wide">Pipeline Source</div>
                        <div className="text-lg font-display font-semibold text-white truncate">{dataSource || 'Loading...'}</div>
                    </div>
                </div>

                {/* Map Visualization */}
                <div className="glass-card">
                    <h4 className="font-display text-xl text-white mb-1">Interactive Temperature Map</h4>
                    <p className="text-sm text-gray-400 mb-4">Click locations to drill down.</p>
                    <div className="w-full h-[500px]">
                        {level === 'global' ? (
                            <Plot
                                data={[{
                                    type: 'choropleth',
                                    locations: currentYearData.map(d => d.Country),
                                    locationmode: 'country names',
                                    z: currentYearData.map(d => d.AvgTemp),
                                    colorscale: 'RdYlBu',
                                    reversescale: true,
                                    zmin: -15,
                                    zmax: 30,
                                    hoverinfo: 'location+z',
                                }]}
                                layout={{
                                    autosize: true,
                                    paper_bgcolor: 'rgba(0,0,0,0)',
                                    plot_bgcolor: 'rgba(0,0,0,0)',
                                    geo: { showframe: false, projection: { type: 'natural earth' }, bgcolor: 'transparent', landcolor: '#1e1e24' },
                                    margin: { l: 0, r: 0, t: 0, b: 0 }
                                }}
                                useResizeHandler={true}
                                style={{ width: '100%', height: '100%' }}
                                onClick={handleMapClick}
                            />
                        ) : (
                            <Plot
                                data={[{
                                    type: 'scattergeo',
                                    locationmode: 'country names',
                                    lat: currentYearData.map(d => parseFloat(d.Latitude?.replace(/[NS]/g, '')) * (d.Latitude?.includes('S') ? -1 : 1)),
                                    lon: currentYearData.map(d => parseFloat(d.Longitude?.replace(/[EW]/g, '')) * (d.Longitude?.includes('W') ? -1 : 1)),
                                    text: currentYearData.map(d => `${d.City}: ${d.AvgTemp}°C`),
                                    hoverinfo: 'text',
                                    mode: 'markers',
                                    marker: {
                                        size: 14,
                                        color: currentYearData.map(d => d.AvgTemp),
                                        colorscale: 'Jet',
                                        cmin: -10, cmax: 35,
                                        showscale: true
                                    }
                                }]}
                                layout={{
                                    autosize: true,
                                    paper_bgcolor: 'rgba(0,0,0,0)',
                                    geo: { scope: level === 'country' ? 'world' : 'world', projection: { type: 'natural earth' }, showland: true, landcolor: '#1e1e24', bgcolor: 'transparent' },
                                    margin: { l: 0, r: 0, t: 0, b: 0 }
                                }}
                                useResizeHandler={true}
                                style={{ width: '100%', height: '100%' }}
                                onClick={handleMapClick}
                            />
                        )}
                    </div>
                </div>

                {/* Trend Chart */}
                <div className="glass-card">
                    <h4 className="font-display text-xl text-white mb-4">Warming Trend Analysis</h4>
                    <div className="w-full h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trendData}>
                                <XAxis dataKey="Year" stroke="#8c8ca3" />
                                <YAxis domain={['auto', 'auto']} stroke="#8c8ca3" />
                                <Tooltip contentStyle={{ backgroundColor: '#1a1a24', border: 'none', borderRadius: '8px', color: '#fff' }} />
                                <ReferenceLine x={activeYear} stroke="#fff" strokeDasharray="3 3" />
                                <Line type="monotone" dataKey="AvgTemp" stroke="rgba(255, 75, 75, 0.3)" strokeWidth={1} dot={false} />
                                <Line type="monotone" dataKey="RollingAvg" name="10-Year Trend" stroke="#ff4b4b" strokeWidth={3} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </main>
        </div>
    );
}