import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const StatsModal = ({ playerName, timingHistory, onClose }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      if (!playerName.trim()) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(`${API_URL}/api/player-stats/${encodeURIComponent(playerName)}`);
        if (response.data.success) {
          setStats(response.data.stats);
        } else {
          setError('Failed to load statistics');
        }
      } catch (error) {
        console.error('Error fetching stats:', error);
        setError('Unable to fetch statistics. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [playerName]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-content">
            <h2>📊 Player Statistics</h2>
            <p className="player-name-display">{playerName}</p>
          </div>
          <button onClick={onClose} className="close-btn" aria-label="Close modal">×</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>Loading statistics...</p>
            </div>
          ) : error ? (
            <div className="error-container">
              <div className="error-icon">⚠️</div>
              <p className="error-message-text">{error}</p>
            </div>
          ) : !stats ? (
            <div className="no-stats-container">
              <div className="no-stats-icon">📭</div>
              <p>No game history found for player: <strong>{playerName}</strong></p>
              <p className="no-stats-hint">Start playing to see your statistics here!</p>
            </div>
          ) : (
            <>
              <div className="stats-grid">
                <div className="stat-card stat-card-primary">
                  <div className="stat-icon">🎮</div>
                  <div className="stat-label">Total Games</div>
                  <div className="stat-value">{stats.totalGames || 0}</div>
                </div>

                <div className="stat-card stat-card-success">
                  <div className="stat-icon">🏆</div>
                  <div className="stat-label">Games Won</div>
                  <div className="stat-value">{stats.wins || 0}</div>
                </div>

                <div className="stat-card stat-card-info">
                  <div className="stat-icon">📈</div>
                  <div className="stat-label">Win Rate</div>
                  <div className="stat-value">{stats.winRate || 0}%</div>
                </div>

                <div className="stat-card stat-card-warning">
                  <div className="stat-icon">⏱️</div>
                  <div className="stat-label">Avg EK Time</div>
                  <div className="stat-value">{stats.avgEkTime || 0} ms</div>
                </div>

                <div className="stat-card stat-card-warning">
                  <div className="stat-icon">⚡</div>
                  <div className="stat-label">Avg Dinic Time</div>
                  <div className="stat-value">{stats.avgDinicTime || 0} ms</div>
                </div>
              </div>

              {timingHistory.length > 0 ? (
                <div className="chart-section">
                  <h3 className="chart-title">
                    <span className="chart-icon">📉</span>
                    Algorithm Performance Comparison
                  </h3>
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={timingHistory} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis 
                          dataKey="round" 
                          stroke="#666"
                          label={{ value: 'Round Number', position: 'insideBottom', offset: -5, style: { fill: '#666' } }}
                        />
                        <YAxis 
                          stroke="#666"
                          label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft', style: { fill: '#666' } }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                            border: '1px solid #ccc',
                            borderRadius: '8px',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                          }}
                        />
                        <Legend 
                          wrapperStyle={{ paddingTop: '20px' }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="ekTime" 
                          stroke="#667eea" 
                          name="Edmonds-Karp"
                          strokeWidth={2}
                          dot={{ fill: '#667eea', r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="dinicTime" 
                          stroke="#82ca9d" 
                          name="Dinic's Algorithm"
                          strokeWidth={2}
                          dot={{ fill: '#82ca9d', r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="no-chart-container">
                  <p className="no-chart-message">No timing data available yet. Complete some rounds to see performance comparison!</p>
                </div>
              )}
            </>
          )}
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  );
};

export default StatsModal;