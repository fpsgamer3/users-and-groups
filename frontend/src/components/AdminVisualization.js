import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import './AdminVisualization.css';
import { useLanguage } from '../LanguageContext';

function AdminVisualization({ onClose }) {
  const { t } = useLanguage();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('graph');
  const svgRef = useRef();

  // Fetch graph data from backend
  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/auth/admin/graph-data/', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });

        if (response.ok) {
          const graphData = await response.json();
          setData(graphData);
        } else if (response.status === 403) {
          setError(t('viz_error'));
        } else {
          setError(t('modal_loading'));
        }
      } catch (err) {
        setError('Error loading graph data');
        console.error('Error fetching graph data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, []);

  // Helper function to get hierarchical position for node based on role
  const getNodeHierarchy = (node, width, height) => {
    // Skip admin nodes - don't show them
    if (node.role === 'admin') return null;
    
    const positions = {
      'teacher': { x: width * 0.15, y: height * 0.25 },
      'moderator': { x: width * 0.35, y: height * 0.35 },
      'student': { x: width * 0.55, y: height * 0.55 },
      'group': { x: width * 0.75, y: height * 0.5 }
    };
    return positions[node.role] || { x: width / 2, y: height / 2 };
  };

  // Draw the graph - only render once when data loads
  useEffect(() => {
    if (!data || !svgRef.current) return;

    const container = svgRef.current.parentElement;
    if (!container) return;

    const width = container.offsetWidth || window.innerWidth;
    const height = container.offsetHeight || window.innerHeight - 150;

    // Clear previous SVG content
    d3.select(svgRef.current).selectAll("*").remove();

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .style('background', 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)');

    // Create a group for zoom/pan
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom()
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Filter out admin nodes
    const filteredNodes = data.nodes.filter(n => n.role !== 'admin');
    const filteredLinks = data.links.filter(link => {
      const sourceNode = data.nodes.find(n => n.id === link.source.id || n.id === link.source);
      const targetNode = data.nodes.find(n => n.id === link.target.id || n.id === link.target);
      return sourceNode?.role !== 'admin' && targetNode?.role !== 'admin';
    });

    // Create simulation with better spacing
    const simulation = d3.forceSimulation(filteredNodes)
      .force('link', d3.forceLink(filteredLinks)
        .id(d => d.id)
        .distance(350)
        .strength(0.08))
      .force('charge', d3.forceManyBody()
        .strength(d => {
          // Much stronger repulsion for more spacing
          return d.type === 'group' ? -1200 : -900;
        })
        .distanceMax(600))
      .force('collision', d3.forceCollide().radius(d => {
        if (d.type === 'group') return 60;
        return 50;
      }))
      .force('x', d3.forceX()
        .x(d => getNodeHierarchy(d, width, height)?.x || width / 2)
        .strength(0.25))
      .force('y', d3.forceY()
        .y(d => getNodeHierarchy(d, width, height)?.y || height / 2)
        .strength(0.25))
      .on('tick', updateGraph);

    // Create links with proper styling
    const link = g.append('g')
      .selectAll('line')
      .data(filteredLinks)
      .join('line')
      .attr('stroke', d => {
        if (d.type === 'creator') return '#666';
        if (d.type === 'admin' || d.type === 'moderator') return '#f59e0b';
        return '#999';
      })
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => {
        if (d.type === 'creator') return 1.5;
        if (d.type === 'admin' || d.type === 'moderator') return 2.5;
        return 1.5;
      })
      .attr('stroke-dasharray', d => {
        if (d.type === 'creator') return '5,5';
        return '0';
      });

    // Create nodes with proper sizing and coloring
    const node = g.append('g')
      .selectAll('circle')
      .data(filteredNodes)
      .join('circle')
      .attr('r', d => {
        if (d.type === 'group') return 40;
        return 30;
      })
      .attr('fill', d => {
        if (d.role === 'teacher') return '#3b82f6';
        if (d.role === 'moderator') return '#f59e0b';
        if (d.role === 'group') return '#10b981';
        return '#8b5cf6';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('filter', d => {
        if (d.is_moderator) return 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.6))';
        return 'drop-shadow(0 0 2px rgba(0, 0, 0, 0.3))';
      })
      .attr('class', d => `node node-${d.id}`)
      .call(drag(simulation));

    // Add interaction tooltips
    node.on('mouseenter', function(event, d) {
      const currentRadius = d.type === 'group' ? 40 : 30;
      const newRadius = currentRadius * 1.4;
      
      d3.select(this)
        .transition()
        .duration(200)
        .attr('r', newRadius)
        .attr('filter', 'drop-shadow(0 0 12px rgba(0, 0, 0, 0.5))');

      // Show tooltip
      svg.append('text')
        .attr('class', `node-tooltip tooltip-${d.id}`)
        .attr('x', d.x || 0)
        .attr('y', (d.y || 0) - 55)
        .text(`${d.label} (${d.role})`)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('font-weight', 'bold')
        .attr('fill', '#1f2937')
        .attr('background', '#fff')
        .attr('pointer-events', 'none')
        .attr('z-index', '1000')
        .style('text-shadow', '0 0 3px white, 0 0 6px white')
        .style('opacity', 0)
        .transition()
        .duration(200)
        .style('opacity', 1);
    })
    .on('mouseleave', function(event, d) {
      const currentRadius = d.type === 'group' ? 40 : 30;
      
      d3.select(this)
        .transition()
        .duration(200)
        .attr('r', currentRadius)
        .attr('filter', d.is_moderator ? 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.6))' : 'drop-shadow(0 0 2px rgba(0, 0, 0, 0.3))');

      svg.selectAll(`.tooltip-${d.id}`)
        .transition()
        .duration(200)
        .style('opacity', 0)
        .remove();
    });

    // Create labels
    const labels = g.append('g')
      .selectAll('text')
      .data(filteredNodes)
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .attr('font-size', d => d.type === 'group' ? '12px' : '10px')
      .attr('font-weight', d => d.type === 'group' || d.role === 'teacher' ? 'bold' : 'normal')
      .attr('fill', '#000')
      .attr('pointer-events', 'none')
      .text(d => {
        if (d.type === 'group') return d.label;
        return d.label.substring(0, 8);
      });

    // Update function for simulation
    function updateGraph() {
      link
        .attr('x1', d => d.source.x || 0)
        .attr('y1', d => d.source.y || 0)
        .attr('x2', d => d.target.x || 0)
        .attr('y2', d => d.target.y || 0);

      node
        .attr('cx', d => d.x || 0)
        .attr('cy', d => d.y || 0);

      labels
        .attr('x', d => d.x || 0)
        .attr('y', d => d.y || 0);
    }

    // Drag behavior - nodes stay where you leave them
    function drag(simulation) {
      function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        // Keep the node at the position where it was dropped
        d.fx = d.x;
        d.fy = d.y;
      }

      return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
    }

    // Cleanup on unmount
    return () => {
      simulation.stop();
    };
  }, [data]);

  if (loading) {
    return (
      <div className="admin-visualization">
        <div className="visualization-header">
          <h1>{t('viz_title')}</h1>
          <button className="btn-back" onClick={onClose}>{t('viz_back')}</button>
        </div>
        <p className="loading">{t('viz_loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-visualization">
        <div className="visualization-header">
          <h1>{t('viz_title')}</h1>
          <button className="btn-back" onClick={onClose}>{t('viz_back')}</button>
        </div>
        <p className="error">{error}</p>
      </div>
    );
  }

  return (
    <div className="admin-visualization">
      <div className="visualization-header">
        <div className="header-content">
          <h1>{t('viz_title')}</h1>
          <div className="legend">
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#3b82f6' }}></span>
              <span>{t('viz_teacher')}</span>
            </div>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#f59e0b' }}></span>
              <span>{t('viz_moderator')}</span>
            </div>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#10b981' }}></span>
              <span>{t('viz_group')}</span>
            </div>
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#8b5cf6' }}></span>
              <span>{t('viz_student')}</span>
            </div>
          </div>
        </div>
        <button className="btn-back" onClick={onClose}>{t('viz_back')}</button>
      </div>

      <div className="visualization-tabs">
        <button 
          className={`tab-button ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          {t('viz_graph')}
        </button>
        <button 
          className={`tab-button ${activeTab === 'table' ? 'active' : ''}`}
          onClick={() => setActiveTab('table')}
        >
          {t('viz_table')}
        </button>
      </div>

      <div className="visualization-content">
        <div className={`graph-container ${activeTab === 'graph' ? 'active' : 'hidden'}`}>
          <svg ref={svgRef} className="graph-svg"></svg>
          <div className="visualization-info">
            <p>📊 Hierarchy (Left to Right): Teachers → Moderators → Students → Groups • Drag nodes to reposition (stays fixed) • Scroll to zoom • Drag canvas to pan</p>
          </div>
        </div>
        <div className={`table-container ${activeTab === 'table' ? 'active' : 'hidden'}`}>
          <div className="table-view">
            <DataTable data={data} />
          </div>
        </div>
      </div>
    </div>
  );
}

// Component for table view
function DataTable({ data }) {
  const { t } = useLanguage();
  if (!data) return null;

  const filteredNodes = data.nodes.filter(n => n.role !== 'admin');
  
  // Group nodes by type and role
  const grouped = {
    teachers: filteredNodes.filter(n => n.role === 'teacher'),
    moderators: filteredNodes.filter(n => n.role === 'moderator'),
    students: filteredNodes.filter(n => n.role === 'student' || n.role === 'moderator'), // Include moderators as they're also students
    groups: filteredNodes.filter(n => n.type === 'group')
  };

  return (
    <div className="data-table-container">
      <div className="summary-sidebar">
        <div className="summary-stat">
          <span className="summary-label">Total</span>
          <span className="summary-value">{grouped.teachers.length + grouped.moderators.length + grouped.students.length + grouped.groups.length}</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Total Groups:</span>
          <span className="summary-value">{grouped.groups.length}</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Teachers:</span>
          <span className="summary-value">{grouped.teachers.length}</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Moderators:</span>
          <span className="summary-value">{grouped.moderators.length}</span>
        </div>
        <div className="summary-stat">
          <span className="summary-label">Students:</span>
          <span className="summary-value">{grouped.students.length}</span>
        </div>
      </div>

      <div className="table-content">
        <div className="data-section">
          <h3 className="section-title teachers-title">[Teachers]</h3>
          {grouped.teachers.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {grouped.teachers.map(node => (
                  <tr key={node.id}>
                    <td>{node.label}</td>
                    <td><span className="role-badge teacher">{node.role}</span></td>
                    <td>{node.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="empty-section">No teachers</p>
          )}
        </div>

        <div className="data-section">
          <h3 className="section-title moderators-title">[Moderators]</h3>
          {grouped.moderators.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {grouped.moderators.map(node => (
                  <tr key={node.id}>
                    <td>{node.label}</td>
                    <td><span className="role-badge moderator">{node.role}</span></td>
                    <td>{node.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="empty-section">{t('viz_no_moderators')}</p>
          )}
        </div>

        <div className="data-section">
          <h3 className="section-title students-title">[{t('viz_student')}s]</h3>
          {grouped.students.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {grouped.students.map(node => (
                  <tr key={node.id}>
                    <td>{node.label}</td>
                    <td><span className="role-badge student">{node.role}</span></td>
                  <td>{node.type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty-section">{t('viz_no_students')}</p>
        )}
        </div>

        <div className="data-section">
          <h3 className="section-title groups-title">[Groups]</h3>
          {grouped.groups.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Group Name</th>
                  <th>Type</th>
                  <th>Members</th>
                </tr>
              </thead>
              <tbody>
                {grouped.groups.map(node => {
                  const memberCount = data.links.filter(
                  link => (link.source.id || link.source) === node.id || (link.target.id || link.target) === node.id
                ).length;
                return (
                  <tr key={node.id}>
                    <td>{node.label}</td>
                    <td>{node.type}</td>
                    <td>{memberCount} members</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p className="empty-section">No groups</p>
        )}
      </div>
      </div>
    </div>
  );
}

export default AdminVisualization;

