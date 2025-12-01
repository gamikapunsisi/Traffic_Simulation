import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const StatsModal = ({ playerName, timingHistory, onClose }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      if (!playerName.trim()) {
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(`${API_URL}/api/player-stats/${encodeURIComponent(playerName)}`);
        if (response.data.success) {
          setStats(response.data.stats);
        }
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [playerName]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Player Statistics</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <p>Loading statistics...</p>
          ) : !stats ? (
            <p>No game history found for player: <strong>{playerName}</strong></p>
          ) : (
            <>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Total Games</div>
                  <div className="stat-value">{stats.totalGames}</div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">Games Won</div>
                  <div className="stat-value">{stats.wins}</div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">Win Rate</div>
                  <div className="stat-value">{stats.winRate}%</div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">Avg EK Time</div>
                  <div className="stat-value">{stats.avgEkTime} ms</div>
                </div>

                <div className="stat-card">
                  <div className="stat-label">Avg Dinic Time</div>
                  <div className="stat-value">{stats.avgDinicTime} ms</div>
                </div>
              </div>

              {timingHistory.length > 0 && (
                <div className="chart-section">
                  <h3>Algorithm Performance Comparison</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={timingHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="round" 
                        label={{ value: 'Round Number', position: 'insideBottom', offset: -5 }}
                      />
                      <YAxis 
                        label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="ekTime" 
                        stroke="#8884d8" 
                        name="Edmonds-Karp"
                        strokeWidth={2}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="dinicTime" 
                        stroke="#82ca9d" 
                        name="Dinic's Algorithm"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
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