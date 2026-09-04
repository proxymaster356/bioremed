export function renderMetrics(summary) {
  const metrics = [
    ["Avg soil pH", summary.avg_soil_ph],
    ["NPK baseline", `${summary.avg_n}/${summary.avg_p}/${summary.avg_k}`],
    ["Pollution cases", summary.pollution_cases],
    ["Potable water", `${summary.potable_water_rate}%`],
  ];
  document.querySelector("#metric-grid").innerHTML = metrics
    .map(([label, value]) => `<article class="metric"><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

export function drawLineChart(canvas, rows) {
  const ctx = canvas.getContext("2d");
  const { width, height } = canvas;
  ctx.clearRect(0, 0, width, height);
  drawFrame(ctx, width, height);
  const values = rows.map((row) => row.ec);
  const min = Math.min(...values) * 0.9;
  const max = Math.max(...values) * 1.1;
  const points = rows.map((row, index) => {
    const x = 54 + (index / Math.max(1, rows.length - 1)) * (width - 94);
    const y = height - 46 - ((row.ec - min) / (max - min || 1)) * (height - 88);
    return { x, y, row };
  });
  ctx.strokeStyle = "#315c9d";
  ctx.lineWidth = 4;
  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.stroke();
  points.forEach((point) => {
    ctx.fillStyle = point.row.forecast ? "#d66a2f" : "#17715b";
    ctx.beginPath();
    ctx.arc(point.x, point.y, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#647067";
    ctx.font = "13px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(point.row.year, point.x, height - 18);
  });
  ctx.fillStyle = "#17211c";
  ctx.font = "14px system-ui";
  ctx.textAlign = "left";
  ctx.fillText("Electrical conductivity", 18, 24);
}

export function drawBarChart(canvas, summary) {
  const ctx = canvas.getContext("2d");
  const { width, height } = canvas;
  ctx.clearRect(0, 0, width, height);
  const bars = [
    ["N", summary.avg_n, "#17715b"],
    ["P", summary.avg_p, "#315c9d"],
    ["K", summary.avg_k, "#d66a2f"],
  ];
  const max = Math.max(...bars.map((bar) => bar[1])) * 1.15;
  bars.forEach(([label, value, color], index) => {
    const barWidth = 70;
    const x = 70 + index * 115;
    const h = (value / max) * (height - 86);
    const y = height - 44 - h;
    ctx.fillStyle = "#eef4ee";
    ctx.fillRect(x, 30, barWidth, height - 74);
    ctx.fillStyle = color;
    ctx.fillRect(x, y, barWidth, h);
    ctx.fillStyle = "#17211c";
    ctx.font = "15px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(label, x + barWidth / 2, height - 18);
    ctx.fillText(String(value), x + barWidth / 2, y - 8);
  });
}

function drawFrame(ctx, width, height) {
  ctx.strokeStyle = "#d9e2d8";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(44, 24);
  ctx.lineTo(44, height - 44);
  ctx.lineTo(width - 22, height - 44);
  ctx.stroke();
}

