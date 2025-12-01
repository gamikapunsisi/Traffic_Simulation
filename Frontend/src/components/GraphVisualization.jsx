import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const GraphVisualization = ({ graphData, flowData, round }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!graphData) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 800;
    const height = 600;
    const margin = { top: 40, right: 40, bottom: 40, left: 40 };

    svg.attr('width', width).attr('height', height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Node positions (custom layout for traffic network)
    const positions = {
      'A': [50, 280],
      'B': [200, 150],
      'C': [200, 280],
      'D': [200, 410],
      'E': [400, 150],
      'F': [400, 340],
      'G': [600, 180],
      'H': [600, 320],
      'T': [750, 250]
    };

    // Create nodes data
    const nodes = graphData.nodes.map(id => ({
      id,
      x: positions[id][0],
      y: positions[id][1]
    }));

    // Create edges data
    const edges = graphData.edges.map(edge => {
      const source = nodes.find(n => n.id === edge.source);
      const target = nodes.find(n => n.id === edge.target);
      const flowKey = `${edge.source}-${edge.target}`;
      const flow = flowData ? (flowData[flowKey] || 0) : 0;
      
      return {
        ...edge,
        source,
        target,
        flow
      };
    });

    // Define arrow marker
    svg.append('defs').selectAll('marker')
      .data(['arrow'])
      .enter().append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');

    // Draw edges
    const maxCapacity = Math.max(...edges.map(e => e.capacity));
    
    g.selectAll('.edge')
      .data(edges)
      .enter()
      .append('line')
      .attr('class', 'edge')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)
      .attr('stroke', d => {
        if (!flowData || d.flow === 0) return '#999';
        const utilization = d.flow / d.capacity;
        if (utilization > 0.8) return '#d9534f'; // Red
        if (utilization > 0.5) return '#f0ad4e'; // Orange
        return '#5bc0de'; // Blue
      })
      .attr('stroke-width', d => {
        if (!flowData) return 2;
        return 2 + (d.flow / maxCapacity) * 6;
      })
      .attr('marker-end', 'url(#arrow)');

    // Draw edge labels
    g.selectAll('.edge-label')
      .data(edges)
      .enter()
      .append('g')
      .attr('class', 'edge-label')
      .attr('transform', d => {
        const midX = (d.source.x + d.target.x) / 2;
        const midY = (d.source.y + d.target.y) / 2;
        return `translate(${midX},${midY})`;
      })
      .each(function(d) {
        const label = d3.select(this);
        
        // Background rect
        label.append('rect')
          .attr('x', -20)
          .attr('y', -10)
          .attr('width', 40)
          .attr('height', 20)
          .attr('fill', 'white')
          .attr('stroke', '#999')
          .attr('rx', 3);
        
        // Label text
        const text = flowData ? `${d.flow}/${d.capacity}` : `${d.capacity}`;
        label.append('text')
          .attr('text-anchor', 'middle')
          .attr('dy', '0.35em')
          .attr('font-size', '11px')
          .attr('font-weight', 'bold')
          .text(text);
      });

    // Draw nodes
    g.selectAll('.node')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('class', 'node')
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
      .attr('r', 25)
      .attr('fill', d => {
        if (d.id === 'A') return '#90EE90'; // Light green
        if (d.id === 'T') return '#FFB6C1'; // Light pink
        return '#FFD700'; // Gold
      })
      .attr('stroke', '#333')
      .attr('stroke-width', 2);

    // Draw node labels
    g.selectAll('.node-label')
      .data(nodes)
      .enter()
      .append('text')
      .attr('class', 'node-label')
      .attr('x', d => d.x)
      .attr('y', d => d.y)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .text(d => d.id);

    // Title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .attr('font-size', '18px')
      .attr('font-weight', 'bold')
      .text(`Traffic Network - Round ${round}${flowData ? ' (Flow Distribution)' : ''}`);

  }, [graphData, flowData, round]);

  return (
    <div className="graph-container">
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default GraphVisualization;