import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

function CandlestickChart({ data = [], markers = [], height = 400 }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      height,
      layout: {
        background: { color: '#1e2d3d' },
        textColor: '#8899a6',
      },
      grid: {
        vertLines: { color: '#2d3748' },
        horzLines: { color: '#2d3748' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#2d3748',
      },
      timeScale: {
        borderColor: '#2d3748',
        timeVisible: true,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#00c853',
      downColor: '#ff1744',
      borderDownColor: '#ff1744',
      borderUpColor: '#00c853',
      wickDownColor: '#ff1744',
      wickUpColor: '#00c853',
    });

    candleSeries.setData(data);

    if (markers.length > 0) {
      candleSeries.setMarkers(markers);
    }

    // Volume histogram
    const volumeData = data.filter(d => d.volume != null).map(d => ({
      time: d.time,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(0, 200, 83, 0.3)' : 'rgba(255, 23, 68, 0.3)',
    }));

    if (volumeData.length > 0) {
      const volumeSeries = chart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: '',
      });
      volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeries.setData(volumeData);
    }

    chart.timeScale().fitContent();
    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, markers, height]);

  if (data.length === 0) {
    return (
      <div style={{
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        color: 'var(--text-muted)',
      }}>
        Sin datos de precio disponibles
      </div>
    );
  }

  return <div ref={chartContainerRef} style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden' }} />;
}

export default CandlestickChart;
