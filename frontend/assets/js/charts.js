// Dynamic Chart.js Rendering Wrappers with custom BI enterprise themes

const Charts = {
    // Shared premium color palette matching CSS design system
    colors: {
        primary: "#0f172a",             /* slate-900 */
        primaryLight: "rgba(15, 23, 42, 0.05)",
        accent: "#0284c7",              /* sky-600 */
        accentHover: "#0369a1",
        accentLight: "rgba(2, 132, 199, 0.12)",
        success: "#10b981",             /* emerald-500 */
        successLight: "rgba(16, 185, 129, 0.12)",
        warning: "#f59e0b",             /* amber-500 */
        warningLight: "rgba(245, 158, 11, 0.12)",
        danger: "#ef4444",              /* red-500 */
        dangerLight: "rgba(239, 68, 68, 0.12)",
        grey: "#64748b",                /* slate-500 */
        border: "#e2e8f0",              /* slate-200 */
        palette: ["#0284c7", "#10b981", "#6366f1", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#ef4444", "#3b82f6", "#10b981"]
    },
    
    // Store active Chart.js instances to destroy old ones on reload
    instances: {},
    
    destroy(id) {
        if (this.instances[id]) {
            this.instances[id].destroy();
            delete this.instances[id];
        }
    },

    getColors() {
        return {
            tickColor: "#64748b",
            fontColor: "#0f172a",
            gridColor: "rgba(148, 163, 184, 0.12)",
            cardBg: "#ffffff"
        };
    },
    
    // 1. Line / Area Chart
    createLineChart(canvasId, labels, data, labelName = "Value") {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, "rgba(2, 132, 199, 0.35)");
        gradient.addColorStop(1, "rgba(2, 132, 199, 0.00)");
        
        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: labelName,
                    data: data,
                    borderColor: this.colors.accent,
                    borderWidth: 3,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: this.colors.accent,
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        padding: 12,
                        backgroundColor: "#0f172a",
                        titleFont: { family: 'Inter', size: 12, weight: 'bold' },
                        bodyFont: { family: 'Inter', size: 12 },
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 10.5 }, color: theme.tickColor }
                    },
                    y: {
                        grid: { color: theme.gridColor },
                        ticks: { font: { family: 'Inter', size: 10.5 }, color: theme.tickColor }
                    }
                }
            }
        });
    },

    // 2. Area Chart Wrapper
    createAreaChart(canvasId, labels, data, labelName = "Revenue") {
        this.createLineChart(canvasId, labels, data, labelName);
    },

    // 3. KPI Sparkline Chart
    createSparkline(canvasId, data, isPositive = true) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");

        const color = isPositive ? this.colors.success : this.colors.danger;

        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map((_, i) => i),
                datasets: [{
                    data: data,
                    borderColor: color,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.45,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: { display: false },
                    y: { display: false }
                }
            }
        });
    },
    
    // 4. Bar Chart
    createBarChart(canvasId, labels, data, labelName = "Value", barColor = null) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();
        
        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: labelName,
                    data: data,
                    backgroundColor: barColor || this.colors.accent,
                    hoverBackgroundColor: this.colors.accentHover,
                    borderRadius: 8,
                    maxBarThickness: 32
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        padding: 12,
                        backgroundColor: "#0f172a",
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 10.5 }, color: theme.tickColor }
                    },
                    y: {
                        grid: { color: theme.gridColor },
                        ticks: { font: { family: 'Inter', size: 10.5 }, color: theme.tickColor }
                    }
                }
            }
        });
    },

    // 5. Horizontal Bar Chart
    createHorizontalBarChart(canvasId, labels, data, labelName = "Value", color = "#6366f1") {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: labelName,
                    data: data,
                    backgroundColor: color,
                    borderRadius: 6,
                    maxBarThickness: 22
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { padding: 12, backgroundColor: "#0f172a", cornerRadius: 8 }
                },
                scales: {
                    x: {
                        grid: { color: theme.gridColor },
                        ticks: { font: { family: 'Inter', size: 10.5 }, color: theme.tickColor }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 10.5 }, color: theme.tickColor }
                    }
                }
            }
        });
    },

    // 6. Stacked Bar Chart
    createStackedBarChart(canvasId, labels, dataset1, dataset2) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: dataset1.label || 'Group A',
                        data: dataset1.data || [],
                        backgroundColor: dataset1.color || "#14b8a6",
                        borderRadius: 4
                    },
                    {
                        label: dataset2.label || 'Group B',
                        data: dataset2.data || [],
                        backgroundColor: dataset2.color || "#ef4444",
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'bottom', labels: { font: { family: 'Inter', size: 10.5 }, color: theme.fontColor } },
                    tooltip: { padding: 12, backgroundColor: "#0f172a", cornerRadius: 8 }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    },
                    y: {
                        stacked: true,
                        grid: { color: theme.gridColor },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    }
                }
            }
        });
    },
    
    // 7. Pie Chart
    createPieChart(canvasId, labels, data) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();
        
        this.instances[canvasId] = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: this.colors.palette,
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { font: { family: 'Inter', size: 10.5 }, color: theme.fontColor, boxWidth: 12, padding: 12 }
                    },
                    tooltip: {
                        padding: 12,
                        backgroundColor: "#0f172a",
                        cornerRadius: 8
                    }
                }
            }
        });
    },
    
    // 8. Donut / Doughnut Chart
    createDoughnutChart(canvasId, labels, data) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();
        
        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [this.colors.accent, this.colors.success, "#6366f1", this.colors.warning, "#ec4899", "#8b5cf6", "#14b8a6"],
                    borderWidth: 2,
                    borderColor: "#ffffff",
                    cutout: "68%"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { font: { family: 'Inter', size: 10.5 }, color: theme.fontColor, boxWidth: 10, padding: 12 }
                    },
                    tooltip: {
                        padding: 12,
                        backgroundColor: "#0f172a",
                        cornerRadius: 8
                    }
                }
            }
        });
    },

    // 9. Scatter Plot
    createScatterPlot(canvasId, dataPoints, labelName = "Sales vs Quantity") {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();

        this.instances[canvasId] = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: labelName,
                    data: dataPoints,
                    backgroundColor: this.colors.accent,
                    borderColor: this.colors.accent,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { padding: 12, backgroundColor: "#0f172a", cornerRadius: 8 }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    },
                    y: {
                        grid: { color: theme.gridColor },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    }
                }
            }
        });
    },

    // 10. Bubble Chart
    createBubbleChart(canvasId, dataPoints) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bubble',
            data: {
                datasets: [{
                    label: 'Product Profitability Matrix',
                    data: dataPoints,
                    backgroundColor: "rgba(99, 102, 241, 0.6)",
                    borderColor: "#6366f1",
                    borderWidth: 1.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        padding: 12,
                        backgroundColor: "#0f172a",
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const p = context.raw;
                                return `Avg Price: ₹${p.x} | Sales: ₹${p.y.toLocaleString()} | Qty: ${p.r * 2}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Average Unit Selling Price (INR)', font: { family: 'Inter', size: 11, weight: 'bold' }, color: theme.tickColor },
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    },
                    y: {
                        title: { display: true, text: 'Total Mapped Sales (INR)', font: { family: 'Inter', size: 11, weight: 'bold' }, color: theme.tickColor },
                        grid: { color: theme.gridColor },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    }
                }
            }
        });
    },

    // 11. Radar Chart
    createRadarChart(canvasId, labels, datasetLabel, dataValues) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();

        this.instances[canvasId] = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: datasetLabel,
                    data: dataValues,
                    backgroundColor: "rgba(139, 92, 246, 0.2)",
                    borderColor: "#8b5cf6",
                    borderWidth: 2,
                    pointBackgroundColor: "#8b5cf6",
                    pointBorderColor: "#ffffff",
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { padding: 12, backgroundColor: "#0f172a", cornerRadius: 8 }
                },
                scales: {
                    r: {
                        angleLines: { color: theme.gridColor },
                        grid: { color: theme.gridColor },
                        pointLabels: { font: { family: 'Inter', size: 10 }, color: theme.fontColor },
                        ticks: { display: false }
                    }
                }
            }
        });
    },

    // 12. Gauge Chart (Half Doughnut for Health Score & Inventory Levels)
    createGaugeChart(canvasId, score = 85, label = "Health Score") {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");

        const color = score >= 75 ? this.colors.success : (score >= 50 ? this.colors.warning : this.colors.danger);
        
        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [label, 'Remaining'],
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [color, "#e2e8f0"],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: 270,
                    cutout: "75%"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
    },

    // 13. Funnel Chart
    createFunnelChart(canvasId, stages = ["Store Visits", "Product Views", "Cart Adds", "Checkout", "Completed Purchase"], counts = [10000, 6800, 3200, 1900, 1450]) {
        this.createHorizontalBarChart(canvasId, stages, counts, "Conversion Funnel", "#0284c7");
    },

    // 14. Pareto Chart
    createParetoChart(canvasId, labels, salesData, cumulativeData) {
        this.destroy(canvasId);
        const el = document.getElementById(canvasId);
        if (!el) return;
        const ctx = el.getContext("2d");
        const theme = this.getColors();

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        type: 'bar',
                        label: 'Sales Revenue (INR)',
                        data: salesData,
                        backgroundColor: "rgba(2, 132, 199, 0.85)",
                        borderRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        type: 'line',
                        label: 'Cumulative Share %',
                        data: cumulativeData,
                        borderColor: this.colors.danger,
                        borderWidth: 3,
                        fill: false,
                        tension: 0.25,
                        pointRadius: 4,
                        pointBackgroundColor: this.colors.danger,
                        yAxisID: 'y2'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'bottom', labels: { font: { family: 'Inter', size: 10.5 }, color: theme.fontColor } },
                    tooltip: { padding: 12, backgroundColor: "#0f172a", cornerRadius: 8 }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: theme.gridColor },
                        ticks: { font: { family: 'Inter', size: 10 }, color: theme.tickColor }
                    },
                    y2: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: 0,
                        max: 100,
                        grid: { drawOnChartArea: false },
                        ticks: {
                            font: { family: 'Inter', size: 10 },
                            color: this.colors.danger,
                            callback: function(value) { return value + "%"; }
                        }
                    }
                }
            }
        });
    }
};
