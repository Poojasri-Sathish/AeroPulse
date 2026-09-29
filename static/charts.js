/**
 * AeroPulse - High-Performance Canvas Chart Engine (Light Theme)
 * Lightweight, zero-dependency canvas visualizer for real-time airfare intelligence.
 */
class AeroCharts {
  static formatCurrency(val) {
    return "₹" + Number(val).toLocaleString("en-IN", { maximumFractionDigits: 0 });
  }

  /**
   * Render Line Chart (Trend & Booking Curves)
   */
  static renderLineChart(canvasId, options) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 25, right: 25, bottom: 35, left: 60 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    
    ctx.clearRect(0, 0, width, height);
    
    const data = options.data || [];
    if (data.length === 0) return;
    
    const xKey = options.xKey || "label";
    const yKey = options.yKey || "value";
    const benchmarkVal = options.benchmarkValue;
    
    let yValues = data.map(d => d[yKey]);
    if (benchmarkVal !== undefined) yValues.push(benchmarkVal);
    let minY = Math.min(...yValues) * 0.96;
    let maxY = Math.max(...yValues) * 1.04;
    if (minY === maxY) { minY -= 5; maxY += 5; }
    
    // Grid Lines & Y-axis labels
    const yTicks = 4;
    ctx.strokeStyle = "#f1f5f9";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#64748b";
    ctx.font = "500 11px Inter, sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    
    for (let i = 0; i <= yTicks; i++) {
      const yVal = minY + ((maxY - minY) * i) / yTicks;
      const yPos = padding.top + chartH - (i / yTicks) * chartH;
      
      ctx.beginPath();
      ctx.moveTo(padding.left, yPos);
      ctx.lineTo(width - padding.right, yPos);
      ctx.stroke();
      
      const label = options.isCurrency ? AeroCharts.formatCurrency(yVal) : yVal.toFixed(1);
      ctx.fillText(label, padding.left - 8, yPos);
    }
    
    // Benchmark Line (Base Index 100.0)
    if (benchmarkVal !== undefined && benchmarkVal >= minY && benchmarkVal <= maxY) {
      const bY = padding.top + chartH - ((benchmarkVal - minY) / (maxY - minY)) * chartH;
      ctx.beginPath();
      ctx.strokeStyle = "#d97706";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.moveTo(padding.left, bY);
      ctx.lineTo(width - padding.right, bY);
      ctx.stroke();
      ctx.setLineDash([]);
      
      ctx.fillStyle = "#b45309";
      ctx.font = "bold 10px Inter, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`Base (100.0)`, width - padding.right - 65, bY - 6);
    }
    
    // Map Points
    const points = data.map((d, idx) => {
      const x = padding.left + (idx / (data.length - 1 || 1)) * chartW;
      const y = padding.top + chartH - ((d[yKey] - minY) / (maxY - minY)) * chartH;
      return { x, y, raw: d };
    });
    
    // Fill Gradient Area
    ctx.beginPath();
    ctx.moveTo(points[0].x, padding.top + chartH);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(points[points.length - 1].x, padding.top + chartH);
    ctx.closePath();
    
    const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, options.fillColor || "rgba(2, 132, 199, 0.16)");
    gradient.addColorStop(1, "rgba(2, 132, 199, 0.0)");
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // Line
    ctx.beginPath();
    ctx.strokeStyle = options.lineColor || "#0284c7";
    ctx.lineWidth = 2.5;
    points.forEach((p, idx) => {
      if (idx === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    ctx.stroke();
    
    // Circles & X Labels
    const step = Math.max(1, Math.ceil(data.length / 8));
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    
    points.forEach((p, idx) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = options.lineColor || "#0284c7";
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      
      if (idx % step === 0 || idx === data.length - 1) {
        ctx.fillStyle = "#64748b";
        ctx.font = "500 11px Inter, sans-serif";
        ctx.fillText(p.raw[xKey], p.x, padding.top + chartH + 8);
      }
    });
  }

  /**
   * Render Horizontal Bar Chart
   */
  static renderBarChart(canvasId, options) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 15, right: 20, bottom: 25, left: 110 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    
    ctx.clearRect(0, 0, width, height);
    
    const data = options.data || [];
    if (data.length === 0) return;
    
    const maxVal = Math.max(...data.map(d => d.value)) * 1.15;
    const barHeight = Math.min(22, (chartH / data.length) * 0.65);
    const barSpacing = chartH / data.length;
    
    data.forEach((item, idx) => {
      const y = padding.top + idx * barSpacing + (barSpacing - barHeight) / 2;
      const barW = (item.value / maxVal) * chartW;
      
      // Track
      ctx.fillStyle = "#f1f5f9";
      ctx.beginPath();
      ctx.roundRect(padding.left, y, chartW, barHeight, 4);
      ctx.fill();
      
      // Active Bar
      ctx.fillStyle = item.color || "#0284c7";
      ctx.beginPath();
      ctx.roundRect(padding.left, y, barW, barHeight, 4);
      ctx.fill();
      
      // Label
      ctx.fillStyle = "#334155";
      ctx.font = "600 11px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(item.label, padding.left - 10, y + barHeight / 2);
      
      // Value
      ctx.fillStyle = "#0f172a";
      ctx.font = "bold 11px JetBrains Mono, monospace";
      ctx.textAlign = "left";
      ctx.fillText(options.isCurrency ? AeroCharts.formatCurrency(item.value) : item.value, padding.left + barW + 8, y + barHeight / 2);
    });
  }

  /**
   * Render Stacked Bar Chart for Airfare Component Breakdown
   */
  static renderStackedFareChart(canvasId, airlines) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 30, bottom: 25, left: 120 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    
    ctx.clearRect(0, 0, width, height);
    if (!airlines || airlines.length === 0) return;
    
    const maxTotal = Math.max(...airlines.map(a => a.avg_fare)) * 1.15;
    const barHeight = Math.min(22, (chartH / airlines.length) * 0.65);
    const barSpacing = chartH / airlines.length;
    
    const colors = {
      base: "#0284c7",
      taxes: "#10b981",
      airport: "#f59e0b",
      fee: "#8b5cf6"
    };
    
    airlines.forEach((airline, idx) => {
      const y = padding.top + idx * barSpacing + (barSpacing - barHeight) / 2;
      let currX = padding.left;
      
      const wBase = (airline.base_fare / maxTotal) * chartW;
      const wTaxes = (airline.taxes / maxTotal) * chartW;
      const wAirport = (airline.airport_fees / maxTotal) * chartW;
      const wFee = (airline.convenience_fee / maxTotal) * chartW;
      
      ctx.fillStyle = colors.base;
      ctx.fillRect(currX, y, wBase, barHeight);
      currX += wBase;
      
      ctx.fillStyle = colors.taxes;
      ctx.fillRect(currX, y, wTaxes, barHeight);
      currX += wTaxes;
      
      ctx.fillStyle = colors.airport;
      ctx.fillRect(currX, y, wAirport, barHeight);
      currX += wAirport;
      
      ctx.fillStyle = colors.fee;
      ctx.fillRect(currX, y, wFee, barHeight);
      currX += wFee;
      
      // Label
      ctx.fillStyle = "#1e293b";
      ctx.font = "600 11px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(airline.airline, padding.left - 10, y + barHeight / 2);
      
      // Total
      ctx.fillStyle = "#0284c7";
      ctx.font = "bold 11px JetBrains Mono, monospace";
      ctx.textAlign = "left";
      ctx.fillText(AeroCharts.formatCurrency(airline.avg_fare), currX + 8, y + barHeight / 2);
    });
  }
}
