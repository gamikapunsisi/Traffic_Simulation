import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GraphVisualization from './components/GraphVisualization';
import ControlPanel from './components/ControlPanel';
import ResultsPanel from './components/ResultsPanel';
import StatsModal from './components/StatsModal';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [graphData, setGraphData] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [guess, setGuess] = useState('');
  const [results, setResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentRound, setCurrentRound] = useState(1);
  const [flowData, setFlowData] = useState(null);
  const [showStats, setShowStats] = useState(false);
  const [timingHistory, setTimingHistory] = useState([]);

  // Load initial graph
  useEffect(() => {
    loadNewGraph();
  }, []);

  const loadNewGraph = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/new-game`);
      if (response.data.success) {
        setGraphData(response.data.graph);
        setCurrentRound(response.data.graph.round);
        setFlowData(null);
        setGuess('');
      }
    } catch (error) {
      console.error('Error loading graph:', error);
      alert('Failed to load new graph. Make sure the backend is running.');
    }
  };

  const handleSubmitGuess = async () => {
    if (!playerName.trim()) {
      alert('Please enter your name');
      return;
    }

    if (!guess || isNaN(guess) || parseInt(guess) < 0) {
      alert('Please enter a valid guess (non-negative number)');
      return;
    }

    setIsProcessing(true);

    try {
      const response = await axios.post(`${API_URL}/api/submit-guess`, {
        playerName: playerName.trim(),
        guess: parseInt(guess)
      });

      if (response.data.success) {
        const result = response.data.result;
        
        // Add to results
        const resultText = `
═══════════════════════════════════════
ROUND ${currentRound} RESULTS
═══════════════════════════════════════
Player: ${playerName}
Your Guess: ${guess}

Algorithm Results:
  Edmonds-Karp: ${result.ekFlow} (Time: ${result.ekTime} ms)
  Dinic: ${result.dinicFlow} (Time: ${result.dinicTime} ms)
${!result.algorithmsAgree ? '\n⚠ WARNING: Algorithms produced different results!' : ''}

${result.isCorrect ? 
  '🎉 CORRECT! You win this round!\nYour answer has been saved to the database.' : 
  `❌ INCORRECT!\nCorrect maximum flow: ${result.correctFlow}`}
═══════════════════════════════════════
`;
        
        setResults(prev => [...prev, resultText]);
        
        // Update flow visualization
        const flowDict = {};
        result.flowData.forEach(({ source, target, flow }) => {
          flowDict[`${source}-${target}`] = flow;
        });
        setFlowData(flowDict);

        // Add to timing history
        setTimingHistory(prev => [...prev, {
          round: currentRound,
          ekTime: result.ekTime,
          dinicTime: result.dinicTime
        }]);

        // Show result dialog
        if (result.isCorrect) {
          alert('🎉 Congratulations! You correctly identified the maximum flow!');
        } else {
          alert(`Try again! The correct answer was ${result.correctFlow}`);
        }
      }
    } catch (error) {
      console.error('Error submitting guess:', error);
      alert('Failed to submit guess. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleNewRound = () => {
    loadNewGraph();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🚗 Traffic Flow Challenge</h1>
        <p>Find the maximum flow from A to T</p>
      </header>

      <div className="app-container">
        <div className="graph-section">
          <GraphVisualization 
            graphData={graphData} 
            flowData={flowData}
            round={currentRound}
          />
        </div>

        <div className="control-section">
          <ControlPanel
            playerName={playerName}
            setPlayerName={setPlayerName}
            guess={guess}
            setGuess={setGuess}
            onSubmit={handleSubmitGuess}
            onNewRound={handleNewRound}
            onShowStats={() => setShowStats(true)}
            isProcessing={isProcessing}
            currentRound={currentRound}
          />

          <ResultsPanel results={results} />
        </div>
      </div>

      {showStats && (
        <StatsModal
          playerName={playerName}
          timingHistory={timingHistory}
          onClose={() => setShowStats(false)}
        />
      )}

      <footer className="app-footer">
        Round {currentRound} | {isProcessing ? 'Computing...' : 'Ready'}
      </footer>
    </div>
  );
}

export default App;