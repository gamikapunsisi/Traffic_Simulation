import React from 'react';

const ControlPanel = ({
  playerName,
  setPlayerName,
  onPlayerNameBlur,
  guess,
  setGuess,
  onGuessBlur,
  onSubmit,
  onNewRound,
  onShowStats,
  isProcessing,
  currentRound,
  playerNameError,
  guessError
}) => {
  const handleKeyPress = (e, action) => {
    if (e.key === 'Enter') {
      action();
    }
  };

  return (
    <div className="control-panel">
      <h2 className="panel-title">Traffic simulation Problem</h2>

      <div className="input-section">
        <label className="input-label">
          <span className="label-text">Player Name:</span>
          <input
            type="text"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            onKeyPress={(e) => handleKeyPress(e, () => document.getElementById('guess-input').focus())}
            onBlur={(e) => {
              onPlayerNameBlur(e.target.value);
            }}
            placeholder="Enter your name"
            className={`input-field ${playerNameError ? 'input-error' : ''}`}
            disabled={isProcessing}
            maxLength={50}
          />
          {playerNameError && (
            <span className="error-message" role="alert">{playerNameError}</span>
          )}
        </label>

        <label className="input-label">
          <span className="label-text">Maximum Flow (A → T):</span>
          <input
            id="guess-input"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            value={guess}
            onChange={(e) => setGuess(e.target.value)}
            onKeyPress={(e) => {
              // Only allow numbers
              if (!/[0-9]/.test(e.key) && e.key !== 'Enter' && e.key !== 'Backspace' && e.key !== 'Delete' && e.key !== 'Tab') {
                e.preventDefault();
              } else {
                handleKeyPress(e, onSubmit);
              }
            }}
            onBlur={(e) => {
              onGuessBlur(e.target.value);
            }}
            placeholder="Enter your guess (numbers only)"
            className={`input-field ${guessError ? 'input-error' : ''}`}
            disabled={isProcessing}
          />
          {guessError && (
            <span className="error-message" role="alert">{guessError}</span>
          )}
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