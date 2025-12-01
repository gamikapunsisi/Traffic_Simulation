import React from 'react';

const ControlPanel = ({
  playerName,
  setPlayerName,
  guess,
  setGuess,
  onSubmit,
  onNewRound,
  onShowStats,
  isProcessing,
  currentRound
}) => {
  const handleKeyPress = (e, action) => {
    if (e.key === 'Enter') {
      action();
    }
  };

  return (
    <div className="control-panel">
      <h2 className="panel-title">Traffic Flow Challenge</h2>

      <div className="input-section">
        <label className="input-label">
          <span className="label-text">Player Name:</span>
          <input
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            onKeyPress={(e) => handleKeyPress(e, () => document.getElementById('guess-input').focus())}
            placeholder="Enter your name"
            className="input-field"
            disabled={isProcessing}
            maxLength={50}
          />
        </label>

        <label className="input-label">
          <span className="label-text">Maximum Flow (A → T):</span>
          <input
            id="guess-input"
            type="number"
            value={guess}
            onChange={(e) => setGuess(e.target.value)}
            onKeyPress={(e) => handleKeyPress(e, onSubmit)}
            placeholder="Enter your guess"
            className="input-field"
            disabled={isProcessing}
            min="0"
            max="1000"
          />
        </label>
      </div>

      <div className="button-group">
        <button
          onClick={onSubmit}
          disabled={isProcessing}
          className="btn btn-primary"
        >
          {isProcessing ? 'Computing...' : 'Submit Guess'}
        </button>

        <button
          onClick={onNewRound}
          disabled={isProcessing}
          className="btn btn-secondary"
        >
          New Round
        </button>

        <button
          onClick={onShowStats}
          disabled={isProcessing || !playerName.trim()}
          className="btn btn-info"
        >
          View Player Stats
        </button>
      </div>

      <div className="info-box">
        <p><strong>How to Play:</strong></p>
        <ol>
          <li>Enter your name</li>
          <li>Analyze the traffic network</li>
          <li>Guess the maximum flow from A to T</li>
          <li>Submit and see if you're correct!</li>
        </ol>
        <p className="info-note">
          Each edge shows its capacity. Find the maximum amount of traffic
          that can flow from source (A) to destination (T).
        </p>
      </div>
    </div>
  );
};

export default ControlPanel;