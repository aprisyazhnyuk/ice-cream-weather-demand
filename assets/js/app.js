"use strict";

const COLORS = {
  ink: "#20312b",
  muted: "#65726d",
  line: "rgba(32,49,43,.14)",
  berry: "#cc4c68",
  berryDark: "#9f304b",
  mint: "#b9dfcd",
  mintDark: "#39765f",
  paper: "#fffdf8",
  blue: "#5d83a8",
};

const state = {
  data: null,
  selectedMarket: "moscow",
};

const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function svgElement(name, attributes = {}, parent = null) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
  if (parent) parent.appendChild(node);
  return node;
}

function linearScale(domainMin, domainMax, rangeMin, rangeMax) {
  const span = domainMax - domainMin || 1;
  return (value) => rangeMin + ((value - domainMin) / span) * (rangeMax - rangeMin);
}

function createSvg(container, width, height, label) {
  container.replaceChildren();
  const svg = svgElement("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": label,
  }, container);
  return svg;
}

function linePath(points) {
  return points.map((point, index) => `${index ? "L" : "M"}${point[0].toFixed(2)},${point[1].toFixed(2)}`).join(" ");
}

function shortLabel(label) {
  return label.split(" · ")[0];
}

function marketById(marketId) {
  return state.data.markets.find((market) => market.market_id === marketId);
}

function seriesFor(marketId) {
  return state.data.series.filter((row) => row.market_id === marketId);
}

function showTooltip(event, html) {
  const tooltip = document.querySelector("#tooltip");
  tooltip.innerHTML = html;
  tooltip.style.left = `${event.clientX}px`;
  tooltip.style.top = `${event.clientY}px`;
  tooltip.setAttribute("aria-hidden", "false");
}

function hideTooltip() {
  document.querySelector("#tooltip").setAttribute("aria-hidden", "true");
}

function renderMetrics() {
  const points = state.data.markets.map((market) => market.scoop_point_c);
  document.querySelector("#market-count").textContent = state.data.metadata.market_count;
  document.querySelector("#observation-count").textContent = state.data.metadata.monthly_observation_count;
  document.querySelector("#scoop-range").textContent = `${Math.min(...points).toFixed(1)}–${Math.max(...points).toFixed(1)}°C`;
}

function renderThresholdChart() {
  const container = document.querySelector("#threshold-chart");
  const width = 900;
  const height = 540;
  const margin = { top: 45, right: 70, bottom: 35, left: 205 };
  const innerWidth = width - margin.left - margin.right;
  const sorted = [...state.data.markets].sort((a, b) => a.scoop_point_c - b.scoop_point_c);
  const x = linearScale(10, 30, margin.left, margin.left + innerWidth);
  const rowHeight = 43;
  const svg = createSvg(container, width, height, "Scoop-point temperature ranking for ten markets");

  [10, 15, 20, 25, 30].forEach((tick) => {
    const tickX = x(tick);
    svgElement("line", { x1: tickX, y1: margin.top - 15, x2: tickX, y2: height - margin.bottom, class: "grid-line" }, svg);
    const label = svgElement("text", { x: tickX, y: 20, "text-anchor": "middle", class: "tick-label" }, svg);
    label.textContent = `${tick}°C`;
  });

  sorted.forEach((market, index) => {
    const y = margin.top + index * rowHeight + rowHeight / 2;
    const group = svgElement("g", {
      class: `threshold-row${market.market_id === state.selectedMarket ? " is-active" : ""}`,
      tabindex: "0",
      role: "button",
      "aria-label": `${market.label}, scoop point ${market.scoop_point_c.toFixed(1)} degrees Celsius`,
    }, svg);
    svgElement("rect", { x: 8, y: y - 18, width: width - 16, height: 36, rx: 8, fill: "transparent", class: "threshold-hit" }, group);
    const label = svgElement("text", { x: margin.left - 18, y: y + 4, "text-anchor": "end", class: "row-label" }, group);
    label.textContent = market.label;
    svgElement("line", { x1: x(10), y1: y, x2: x(market.scoop_point_c), y2: y, class: "threshold-stem" }, group);
    svgElement("circle", { cx: x(market.scoop_point_c), cy: y, r: 7, class: "threshold-dot" }, group);
    const value = svgElement("text", { x: x(market.scoop_point_c) + 13, y: y + 4, class: "row-value" }, group);
    value.textContent = `${market.scoop_point_c.toFixed(1)}°`;
    const select = () => selectMarket(market.market_id);
    group.addEventListener("click", select);
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        select();
      }
    });
    group.addEventListener("mousemove", (event) => showTooltip(event, `<strong>${market.scoop_point_c.toFixed(1)}°C</strong><br>${market.label}<br>Peak interest: ${market.peak_interest_month}`));
    group.addEventListener("mouseleave", hideTooltip);
  });

  const note = svgElement("text", { x: margin.left, y: height - 5, class: "chart-note" }, svg);
  note.textContent = "Colder ← temperature where fitted interest reaches half-rise → warmer";
}

function renderSelectionCard() {
  const market = marketById(state.selectedMarket);
  document.querySelector("#selected-label").textContent = market.label;
  document.querySelector("#selected-scoop").textContent = market.scoop_point_c.toFixed(1);
  document.querySelector("#selected-peak").textContent = market.peak_interest_month;
  document.querySelector("#selected-seasonal").textContent = market.seasonal_correlation.toFixed(2);
  document.querySelector("#selected-anomaly").textContent = market.anomaly_correlation.toFixed(2);
  const strength = market.anomaly_response_strength;
  document.querySelector("#selected-copy").textContent = `Interest reaches half of its fitted seasonal rise here. Its warmer-than-usual response is ${strength}.`;
}

function renderControls() {
  const controls = document.querySelector("#market-controls");
  controls.replaceChildren();
  [...state.data.markets].sort((a, b) => a.label.localeCompare(b.label)).forEach((market) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `market-button${market.market_id === state.selectedMarket ? " is-active" : ""}`;
    button.textContent = shortLabel(market.label);
    button.setAttribute("aria-pressed", market.market_id === state.selectedMarket ? "true" : "false");
    button.addEventListener("click", () => selectMarket(market.market_id));
    controls.appendChild(button);
  });
}

function drawAxes(svg, dimensions, xTicks, yTicks, x, y, xSuffix = "", ySuffix = "") {
  const { width, height, margin } = dimensions;
  xTicks.forEach((tick) => {
    const px = x(tick);
    svgElement("line", { x1: px, y1: margin.top, x2: px, y2: height - margin.bottom, class: "grid-line" }, svg);
    const label = svgElement("text", { x: px, y: height - 17, "text-anchor": "middle", class: "tick-label" }, svg);
    label.textContent = `${tick}${xSuffix}`;
  });
  yTicks.forEach((tick) => {
    const py = y(tick);
    svgElement("line", { x1: margin.left, y1: py, x2: width - margin.right, y2: py, class: "grid-line" }, svg);
    const label = svgElement("text", { x: margin.left - 10, y: py + 4, "text-anchor": "end", class: "tick-label" }, svg);
    label.textContent = `${tick}${ySuffix}`;
  });
}

function binnedTrend(rows, binCount = 8) {
  const temperatures = rows.map((row) => row.temperature_c);
  const min = Math.min(...temperatures);
  const max = Math.max(...temperatures);
  const step = (max - min) / binCount || 1;
  return Array.from({ length: binCount }, (_, index) => {
    const start = min + index * step;
    const end = index === binCount - 1 ? max + 0.001 : start + step;
    const bin = rows.filter((row) => row.temperature_c >= start && row.temperature_c < end);
    if (!bin.length) return null;
    return {
      temperature_c: bin.reduce((sum, row) => sum + row.temperature_c, 0) / bin.length,
      interest_index: bin.reduce((sum, row) => sum + row.interest_index, 0) / bin.length,
    };
  }).filter(Boolean);
}

function renderResponseChart() {
  const container = document.querySelector("#response-chart");
  const market = marketById(state.selectedMarket);
  const rows = seriesFor(state.selectedMarket);
  const width = 720;
  const height = 430;
  const margin = { top: 26, right: 25, bottom: 55, left: 56 };
  const temperatures = rows.map((row) => row.temperature_c);
  const minTemp = Math.floor(Math.min(...temperatures) / 5) * 5;
  const maxTemp = Math.ceil(Math.max(...temperatures) / 5) * 5;
  const x = linearScale(minTemp, maxTemp, margin.left, width - margin.right);
  const y = linearScale(0, 100, height - margin.bottom, margin.top);
  const svg = createSvg(container, width, height, `${market.label}: monthly temperature and Google search interest`);
  const xTicks = [];
  for (let value = minTemp; value <= maxTemp; value += 5) xTicks.push(value);
  drawAxes(svg, { width, height, margin }, xTicks, [0, 25, 50, 75, 100], x, y, "°", "");

  const scoopX = x(market.scoop_point_c);
  svgElement("line", { x1: scoopX, y1: margin.top, x2: scoopX, y2: height - margin.bottom, class: "scoop-rule" }, svg);
  const scoopLabel = svgElement("text", { x: scoopX + 6, y: margin.top + 12, class: "axis-label" }, svg);
  scoopLabel.textContent = `scoop point ${market.scoop_point_c.toFixed(1)}°`;

  rows.forEach((row) => {
    const date = new Date(`${row.period}T00:00:00`);
    const circle = svgElement("circle", { cx: x(row.temperature_c), cy: y(row.interest_index), r: 4.6, class: "point" }, svg);
    circle.addEventListener("mousemove", (event) => showTooltip(event, `<strong>${monthNames[date.getUTCMonth()]} ${date.getUTCFullYear()}</strong><br>${row.temperature_c.toFixed(1)}°C · interest ${row.interest_index.toFixed(1)}`));
    circle.addEventListener("mouseleave", hideTooltip);
  });

  const trend = binnedTrend(rows).map((row) => [x(row.temperature_c), y(row.interest_index)]);
  svgElement("path", { d: linePath(trend), class: "trend-path" }, svg);
  const xLabel = svgElement("text", { x: (margin.left + width - margin.right) / 2, y: height - 2, "text-anchor": "middle", class: "axis-label" }, svg);
  xLabel.textContent = "Monthly mean temperature (°C)";
  const yLabel = svgElement("text", { x: 15, y: height / 2, transform: `rotate(-90 15 ${height / 2})`, "text-anchor": "middle", class: "axis-label" }, svg);
  yLabel.textContent = "Relative search interest";
}

function monthlyAverages(rows) {
  return monthNames.map((name, monthIndex) => {
    const monthRows = rows.filter((row) => new Date(`${row.period}T00:00:00`).getUTCMonth() === monthIndex);
    return {
      month: name,
      temperature_c: monthRows.reduce((sum, row) => sum + row.temperature_c, 0) / monthRows.length,
      interest_index: monthRows.reduce((sum, row) => sum + row.interest_index, 0) / monthRows.length,
    };
  });
}

function renderSeasonalChart() {
  const container = document.querySelector("#seasonal-chart");
  const market = marketById(state.selectedMarket);
  const monthly = monthlyAverages(seriesFor(state.selectedMarket));
  const width = 560;
  const height = 430;
  const margin = { top: 28, right: 52, bottom: 48, left: 48 };
  const minTemp = Math.floor(Math.min(...monthly.map((row) => row.temperature_c)) / 5) * 5;
  const maxTemp = Math.ceil(Math.max(...monthly.map((row) => row.temperature_c)) / 5) * 5;
  const x = linearScale(0, 11, margin.left, width - margin.right);
  const yInterest = linearScale(0, 100, height - margin.bottom, margin.top);
  const yTemp = linearScale(minTemp, maxTemp, height - margin.bottom, margin.top);
  const svg = createSvg(container, width, height, `${market.label}: average seasonal cycle for temperature and ice-cream interest`);

  [0, 25, 50, 75, 100].forEach((tick) => {
    const py = yInterest(tick);
    svgElement("line", { x1: margin.left, y1: py, x2: width - margin.right, y2: py, class: "grid-line" }, svg);
    const label = svgElement("text", { x: margin.left - 8, y: py + 4, "text-anchor": "end", class: "tick-label" }, svg);
    label.textContent = tick;
  });
  monthly.forEach((row, index) => {
    const label = svgElement("text", { x: x(index), y: height - 18, "text-anchor": "middle", class: "tick-label" }, svg);
    label.textContent = row.month;
  });
  [minTemp, (minTemp + maxTemp) / 2, maxTemp].forEach((tick) => {
    const label = svgElement("text", { x: width - margin.right + 8, y: yTemp(tick) + 4, class: "tick-label" }, svg);
    label.textContent = `${tick.toFixed(0)}°`;
  });

  const interestPoints = monthly.map((row, index) => [x(index), yInterest(row.interest_index)]);
  const tempPoints = monthly.map((row, index) => [x(index), yTemp(row.temperature_c)]);
  svgElement("path", { d: linePath(interestPoints), class: "interest-path" }, svg);
  svgElement("path", { d: linePath(tempPoints), class: "temperature-path" }, svg);
  monthly.forEach((row, index) => {
    const interestPoint = svgElement("circle", { cx: x(index), cy: yInterest(row.interest_index), r: 4, class: "interest-point" }, svg);
    const temperaturePoint = svgElement("circle", { cx: x(index), cy: yTemp(row.temperature_c), r: 4, class: "temperature-point" }, svg);
    const tooltip = (event) => showTooltip(event, `<strong>${row.month}</strong><br>${row.temperature_c.toFixed(1)}°C · interest ${row.interest_index.toFixed(1)}`);
    [interestPoint, temperaturePoint].forEach((point) => {
      point.addEventListener("mousemove", tooltip);
      point.addEventListener("mouseleave", hideTooltip);
    });
  });
}

function renderAnomalyChart() {
  const container = document.querySelector("#anomaly-chart");
  const width = 760;
  const height = 510;
  const margin = { top: 35, right: 60, bottom: 38, left: 160 };
  const rows = [...state.data.markets].sort((a, b) => b.anomaly_correlation - a.anomaly_correlation);
  const x = linearScale(-0.1, 0.7, margin.left, width - margin.right);
  const rowHeight = 41;
  const svg = createSvg(container, width, height, "Correlation of unusually warm months with unusually high ice-cream interest");

  [-0.1, 0, 0.2, 0.4, 0.6].forEach((tick) => {
    const px = x(tick);
    svgElement("line", { x1: px, y1: margin.top - 12, x2: px, y2: height - margin.bottom, class: tick === 0 ? "axis-line" : "grid-line" }, svg);
    const label = svgElement("text", { x: px, y: 18, "text-anchor": "middle", class: "tick-label" }, svg);
    label.textContent = tick.toFixed(1);
  });

  rows.forEach((market, index) => {
    const y = margin.top + index * rowHeight + 14;
    const label = svgElement("text", { x: margin.left - 12, y: y + 4, "text-anchor": "end", class: "row-label" }, svg);
    label.textContent = shortLabel(market.label);
    const start = x(Math.min(0, market.anomaly_correlation));
    const end = x(Math.max(0, market.anomaly_correlation));
    const bar = svgElement("rect", {
      x: start,
      y: y - 8,
      width: Math.max(2, end - start),
      height: 16,
      rx: 8,
      class: `anomaly-bar ${market.anomaly_response_strength}`,
    }, svg);
    const value = svgElement("text", { x: end + 8, y: y + 4, class: "row-value" }, svg);
    value.textContent = market.anomaly_correlation.toFixed(2);
    bar.addEventListener("mousemove", (event) => showTooltip(event, `<strong>${market.anomaly_correlation.toFixed(2)}</strong><br>${market.label}<br>${market.anomaly_response_strength} anomaly response`));
    bar.addEventListener("mouseleave", hideTooltip);
  });
  const note = svgElement("text", { x: margin.left, y: height - 5, class: "chart-note" }, svg);
  note.textContent = "Pearson correlation after removing each market’s normal month-of-year cycle";
}

function selectMarket(marketId) {
  state.selectedMarket = marketId;
  renderThresholdChart();
  renderSelectionCard();
  renderControls();
  renderResponseChart();
  renderSeasonalChart();
}

function renderAll() {
  renderMetrics();
  renderThresholdChart();
  renderSelectionCard();
  renderControls();
  renderResponseChart();
  renderSeasonalChart();
  renderAnomalyChart();
}

fetch("data/processed/chart_data.json")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((data) => {
    state.data = data;
    renderAll();
  })
  .catch((error) => {
    console.error("Visualization data failed to load", error);
    document.querySelector("#load-error").hidden = false;
  });
