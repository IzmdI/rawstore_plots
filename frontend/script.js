// Конфигурация
const CONFIG = {
    colors: {
        read_iops: "#1f77b4",
        write_iops: "#d62728",
        read_latency: "#2ca02c",
        write_latency: "#ff7f0e"
    },
    margins: {
        top: 60,
        right: 80,
        bottom: 100,
        left: 80
    },
    animationDuration: 300
};

class FIODashboard {
    constructor() {
        this.data = [];
        this.zoomState = {
            scale: 1,
            translate: [0, 0],
            isZoomed: false
        };
        this.init();
    }

    async init() {
        await this.loadData();
        this.createCharts();
        this.setupEventListeners();
        this.updateDataInfo();
    }

    async loadData() {
        try {
            const response = await fetch('data/fio_summary.jsonl');
            if (!response.ok) throw new Error('File not found');
            
            const text = await response.text();
            const lines = text.split('\n').filter(line => line.trim());
            
            this.data = lines.map((line, index) => {
                try {
                    const record = JSON.parse(line);
                    return {
                        id: index,
                        timestamp: record.timestamp,
                        time: new Date(record.timestamp * 1000),
                        timeLabel: new Date(record.timestamp * 1000).toLocaleString('ru-RU'),
                        read_iops: record.read_iops,
                        write_iops: record.write_iops,
                        read_latency: record.read_latency_ns,
                        write_latency: record.write_latency_ns
                    };
                } catch (e) {
                    console.warn('Invalid JSON line:', line);
                    return null;
                }
            }).filter(Boolean);

            if (this.data.length === 0) {
                throw new Error('No valid data found');
            }

        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Ошибка загрузки данных. Проверьте файл data/fio_summary.jsonl');
        }
    }

    createCharts() {
        if (this.data.length === 0) return;

        this.createIOPSChart();
        this.createLatencyChart();
        this.createLegends();
    }

    createIOPSChart() {
        const container = d3.select('#iops-chart .chart-content');
        container.html('');

        const width = container.node().offsetWidth;
        const height = 500;
        const innerWidth = width - CONFIG.margins.left - CONFIG.margins.right;
        const innerHeight = height - CONFIG.margins.top - CONFIG.margins.bottom;

        const svg = container.append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('class', 'iops-svg');

        const g = svg.append('g')
            .attr('transform', `translate(${CONFIG.margins.left},${CONFIG.margins.top})`);

        // Scales
        const xScale = d3.scaleBand()
            .domain(this.data.map(d => d.timeLabel))
            .range([0, innerWidth])
            .padding(0.3);

        const yScale = d3.scaleLinear()
            .domain([0, d3.max(this.data, d => Math.max(d.read_iops, d.write_iops)) * 1.1])
            .range([innerHeight, 0]);

        // Axes
        const xAxis = d3.axisBottom(xScale);
        const yAxis = d3.axisLeft(yScale).ticks(8);

        g.append('g')
            .attr('transform', `translate(0,${innerHeight})`)
            .call(xAxis)
            .selectAll('text')
            .style('text-anchor', 'end')
            .attr('dx', '-.8em')
            .attr('dy', '.15em')
            .attr('transform', 'rotate(-45)');

        g.append('g').call(yAxis);

        // Grid
        g.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat(''));

        // Bars
        const barWidth = xScale.bandwidth() / 2;

        // Read IOPS
        g.selectAll('.read-iops')
            .data(this.data)
            .enter()
            .append('rect')
            .attr('class', 'bar read-iops')
            .attr('x', d => xScale(d.timeLabel))
            .attr('y', d => yScale(d.read_iops))
            .attr('width', barWidth)
            .attr('height', d => innerHeight - yScale(d.read_iops))
            .attr('fill', CONFIG.colors.read_iops)
            .on('mouseover', (event, d) => this.showTooltip(event, d, 'read_iops', 'IOPS'))
            .on('mouseout', () => this.hideTooltip());

        // Write IOPS
        g.selectAll('.write-iops')
            .data(this.data)
            .enter()
            .append('rect')
            .attr('class', 'bar write-iops')
            .attr('x', d => xScale(d.timeLabel) + barWidth)
            .attr('y', d => yScale(d.write_iops))
            .attr('width', barWidth)
            .attr('height', d => innerHeight - yScale(d.write_iops))
            .attr('fill', CONFIG.colors.write_iops)
            .on('mouseover', (event, d) => this.showTooltip(event, d, 'write_iops', 'IOPS'))
            .on('mouseout', () => this.hideTooltip());

        // Labels
        g.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 0 - CONFIG.margins.left)
            .attr('x', 0 - (innerHeight / 2))
            .attr('dy', '1em')
            .style('text-anchor', 'middle')
            .text('IOPS')
            .style('font-weight', 'bold');

        // Zoom behavior
        this.setupZoom(svg, g, xScale, yScale, innerWidth, innerHeight);
    }

    createLatencyChart() {
        const container = d3.select('#latency-chart .chart-content');
        container.html('');

        const width = container.node().offsetWidth;
        const height = 500;
        const innerWidth = width - CONFIG.margins.left - CONFIG.margins.right;
        const innerHeight = height - CONFIG.margins.top - CONFIG.margins.bottom;

        const svg = container.append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('class', 'latency-svg');

        const g = svg.append('g')
            .attr('transform', `translate(${CONFIG.margins.left},${CONFIG.margins.top})`);

        // Scales
        const xScale = d3.scaleBand()
            .domain(this.data.map(d => d.timeLabel))
            .range([0, innerWidth])
            .padding(0.3);

        const yScale = d3.scaleLinear()
            .domain([0, d3.max(this.data, d => Math.max(d.read_latency, d.write_latency)) * 1.1])
            .range([innerHeight, 0]);

        // Axes
        const xAxis = d3.axisBottom(xScale);
        const yAxis = d3.axisLeft(yScale).ticks(8);

        g.append('g')
            .attr('transform', `translate(0,${innerHeight})`)
            .call(xAxis)
            .selectAll('text')
            .style('text-anchor', 'end')
            .attr('dx', '-.8em')
            .attr('dy', '.15em')
            .attr('transform', 'rotate(-45)');

        g.append('g').call(yAxis);

        // Grid
        g.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat(''));

        // Bars
        const barWidth = xScale.bandwidth() / 2;

        // Read Latency
        g.selectAll('.read-latency')
            .data(this.data)
            .enter()
            .append('rect')
            .attr('class', 'bar read-latency')
            .attr('x', d => xScale(d.timeLabel))
            .attr('y', d => yScale(d.read_latency))
            .attr('width', barWidth)
            .attr('height', d => innerHeight - yScale(d.read_latency))
            .attr('fill', CONFIG.colors.read_latency)
            .on('mouseover', (event, d) => this.showTooltip(event, d, 'read_latency', 'ns'))
            .on('mouseout', () => this.hideTooltip());

        // Write Latency
        g.selectAll('.write-latency')
            .data(this.data)
            .enter()
            .append('rect')
            .attr('class', 'bar write-latency')
            .attr('x', d => xScale(d.timeLabel) + barWidth)
            .attr('y', d => yScale(d.write_latency))
            .attr('width', barWidth)
            .attr('height', d => innerHeight - yScale(d.write_latency))
            .attr('fill', CONFIG.colors.write_latency)
            .on('mouseover', (event, d) => this.showTooltip(event, d, 'write_latency', 'ns'))
            .on('mouseout', () => this.hideTooltip());

        // Labels
        g.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 0 - CONFIG.margins.left)
            .attr('x', 0 - (innerHeight / 2))
            .attr('dy', '1em')
            .style('text-anchor', 'middle')
            .text('Latency (ns)')
            .style('font-weight', 'bold');

        // Zoom behavior
        this.setupZoom(svg, g, xScale, yScale, innerWidth, innerHeight);
    }

    setupZoom(svg, g, xScale, yScale, width, height) {
        const zoom = d3.zoom()
            .scaleExtent([0.5, 10])
            .translateExtent([[0, 0], [width, height]])
            .on('zoom', (event) => {
                this.zoomState.isZoomed = true;
                g.attr('transform', event.transform);
            });

        svg.call(zoom);

        // Zoom buttons functionality
        d3.select('#zoom-in').on('click', () => {
            svg.transition().duration(CONFIG.animationDuration).call(zoom.scaleBy, 1.5);
        });

        d3.select('#zoom-out').on('click', () => {
            svg.transition().duration(CONFIG.animationDuration).call(zoom.scaleBy, 0.5);
        });

        d3.select('#reset-zoom').on('click', () => {
            svg.transition().duration(CONFIG.animationDuration).call(zoom.transform, d3.zoomIdentity);
            this.zoomState.isZoomed = false;
        });
    }

    showTooltip(event, d, metric, unit) {
        const tooltip = d3.select('#tooltip');
        const value = d[metric];
        const metricName = metric.replace('_', ' ');

        tooltip.html(`
            <h3>${d.timeLabel}</h3>
            <p><strong>${metricName}:</strong> ${value.toLocaleString()} ${unit}</p>
            <p><strong>Timestamp:</strong> ${d.timestamp}</p>
        `)
        .style('left', (event.pageX + 15) + 'px')
        .style('top', (event.pageY - 15) + 'px')
        .style('display', 'block');
    }

    hideTooltip() {
        d3.select('#tooltip').style('display', 'none');
    }

    createLegends() {
        const iopsLegend = d3.select('#iops-legend');
        const latencyLegend = d3.select('#latency-legend');

        iopsLegend.html('');
        latencyLegend.html('');

        ['read_iops', 'write_iops'].forEach(metric => {
            iopsLegend.append('div')
                .attr('class', 'legend-item')
                .html(`
                    <div class="legend-color" style="background: ${CONFIG.colors[metric]}"></div>
                    <span>${metric.replace('_', ' ')}</span>
                `);
        });

        ['read_latency', 'write_latency'].forEach(metric => {
            latencyLegend.append('div')
                .attr('class', 'legend-item')
                .html(`
                    <div class="legend-color" style="background: ${CONFIG.colors[metric]}"></div>
                    <span>${metric.replace('_', ' ')}</span>
                `);
        });
    }

    updateDataInfo() {
        const info = d3.select('#data-info');
        const lastUpdate = this.data.length > 0 ? 
            this.data[this.data.length - 1].time.toLocaleString('ru-RU') : 
            'Нет данных';
        
        info.text(`Записей: ${this.data.length} | Последнее обновление: ${lastUpdate}`);
        d3.select('#last-update').text(new Date().toLocaleString('ru-RU'));
    }

    showError(message) {
        d3.select('#data-info').text(message).style('color', '#e74c3c');
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.createCharts();
        });
    }
}

// Инициализация дашборда
document.addEventListener('DOMContentLoaded', () => {
    new FIODashboard();
});