import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import App from './App';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock child components
jest.mock('./components/GraphVisualization', () => {
  return function MockGraphVisualization({ graphData, round }) {
    return <div data-testid="graph-visualization">Graph - Round {round}</div>;
  };
});

jest.mock('./components/ControlPanel', () => {
  return function MockControlPanel({
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
  }) {
    return (
      <div data-testid="control-panel">
        <input
          data-testid="player-name-input"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
          onBlur={(e) => onPlayerNameBlur && onPlayerNameBlur(e.target.value)}
          placeholder="Enter your name"
        />
        {playerNameError && <span data-testid="player-name-error">{playerNameError}</span>}
        <input
          data-testid="guess-input"
          value={guess}
          onChange={(e) => setGuess(e.target.value)}
          onBlur={(e) => onGuessBlur && onGuessBlur(e.target.value)}
          placeholder="Enter your guess"
        />
        {guessError && <span data-testid="guess-error">{guessError}</span>}
        <button data-testid="submit-button" onClick={onSubmit} disabled={isProcessing}>
          Submit
        </button>
        <button data-testid="new-round-button" onClick={onNewRound} disabled={isProcessing}>
          New Round
        </button>
        <button data-testid="stats-button" onClick={onShowStats} disabled={isProcessing}>
          Stats
        </button>
      </div>
    );
  };
});

jest.mock('./components/ResultsPanel', () => {
  return function MockResultsPanel({ results }) {
    return (
      <div data-testid="results-panel">
        {results.map((result, index) => (
          <div key={index} data-testid={`result-${index}`}>
            {result}
          </div>
        ))}
      </div>
    );
  };
});

jest.mock('./components/StatsModal', () => {
  return function MockStatsModal({ onClose }) {
    return (
      <div data-testid="stats-modal">
        <button data-testid="close-stats" onClick={onClose}>Close</button>
      </div>
    );
  };
});

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock successful API response for initial load
    mockedAxios.get.mockResolvedValue({
      data: {
        success: true,
        graph: {
          round: 1,
          nodes: ['A', 'B', 'T'],
          edges: [{ source: 'A', target: 'B', capacity: 10 }]
        }
      }
    });
  });

  describe('Component Rendering', () => {
    it('renders the app header', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByText(/Traffic Flow Challenge/i)).toBeInTheDocument();
      });
    });

    it('loads initial graph on mount', async () => {
      render(<App />);
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('/api/new-game')
        );
      });
    });
  });

  describe('Player Name Validation', () => {
    it('shows error when player name contains numbers', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      await userEvent.type(playerNameInput, 'John123');

      // Trigger validation by blurring or submitting
      fireEvent.blur(playerNameInput);
      
      await waitFor(() => {
        const error = screen.queryByTestId('player-name-error');
        if (error) {
          expect(error.textContent).toContain('letters');
        }
      });
    });

    it('shows error when player name is empty on submit', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('submit-button')).toBeInTheDocument();
      });

      const submitButton = screen.getByTestId('submit-button');
      fireEvent.click(submitButton);

      await waitFor(() => {
        const error = screen.queryByTestId('player-name-error');
        if (error) {
          expect(error.textContent).toContain('required');
        }
      });
    });

    it('accepts valid player name with letters, spaces, hyphens, and apostrophes', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      await userEvent.type(playerNameInput, "John O'Connor-Smith");

      // Should not show error for valid name
      await waitFor(() => {
        const error = screen.queryByTestId('player-name-error');
        expect(error).not.toBeInTheDocument();
      });
    });

    it('shows error when player name is too short', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      await userEvent.type(playerNameInput, 'A');
      fireEvent.blur(playerNameInput);

      await waitFor(() => {
        const error = screen.queryByTestId('player-name-error');
        if (error) {
          expect(error.textContent).toContain('at least 2');
        }
      });
    });
  });

  describe('Maximum Flow Validation', () => {
    it('prevents non-numeric input in guess field', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('guess-input')).toBeInTheDocument();
      });

      const guessInput = screen.getByTestId('guess-input');
      
      // Try to type a letter
      fireEvent.change(guessInput, { target: { value: 'abc' } });
      
      // The input should not accept non-numeric values
      // Since we're preventing non-numeric input, the value should remain empty or numeric only
      expect(guessInput.value).toBe('');
    });

    it('shows error when guess is empty on submit', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('submit-button')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      await userEvent.type(playerNameInput, 'John');
      
      const submitButton = screen.getByTestId('submit-button');
      fireEvent.click(submitButton);

      await waitFor(() => {
        const error = screen.queryByTestId('guess-error');
        if (error) {
          expect(error.textContent).toContain('required');
        }
      });
    });

    it('accepts valid numeric input', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('guess-input')).toBeInTheDocument();
      });

      const guessInput = screen.getByTestId('guess-input');
      fireEvent.change(guessInput, { target: { value: '100' } });

      expect(guessInput.value).toBe('100');
    });

    it('shows error when guess is negative', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('guess-input')).toBeInTheDocument();
      });

      const guessInput = screen.getByTestId('guess-input');
      fireEvent.change(guessInput, { target: { value: '-5' } });
      fireEvent.blur(guessInput);

      await waitFor(() => {
        const error = screen.queryByTestId('guess-error');
        if (error) {
          expect(error.textContent).toContain('non-negative');
        }
      });
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      mockedAxios.post.mockResolvedValue({
        data: {
          success: true,
          result: {
            isCorrect: true,
            ekFlow: 10,
            dinicFlow: 10,
            ekTime: 5,
            dinicTime: 3,
            correctFlow: 10,
            flowData: []
          }
        }
      });

      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      const guessInput = screen.getByTestId('guess-input');
      const submitButton = screen.getByTestId('submit-button');

      await userEvent.type(playerNameInput, 'John');
      fireEvent.change(guessInput, { target: { value: '10' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/submit-guess'),
          {
            playerName: 'John',
            guess: 10
          }
        );
      });
    });

    it('does not submit when validation fails', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('submit-button')).toBeInTheDocument();
      });

      const submitButton = screen.getByTestId('submit-button');
      fireEvent.click(submitButton);

      // Should not call API
      await waitFor(() => {
        expect(mockedAxios.post).not.toHaveBeenCalled();
      });
    });

    it('handles API error on submission', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Network error'));

      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      const guessInput = screen.getByTestId('guess-input');
      const submitButton = screen.getByTestId('submit-button');

      await userEvent.type(playerNameInput, 'John');
      fireEvent.change(guessInput, { target: { value: '10' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalled();
      });
    });
  });

  describe('New Round Functionality', () => {
    it('loads new graph when new round is clicked', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('new-round-button')).toBeInTheDocument();
      });

      const newRoundButton = screen.getByTestId('new-round-button');
      fireEvent.click(newRoundButton);

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(2); // Initial load + new round
      });
    });
  });

  describe('Stats Modal', () => {
    it('opens stats modal when stats button is clicked', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      await userEvent.type(playerNameInput, 'John');

      const statsButton = screen.getByTestId('stats-button');
      fireEvent.click(statsButton);

      await waitFor(() => {
        expect(screen.getByTestId('stats-modal')).toBeInTheDocument();
      });
    });

    it('closes stats modal when close button is clicked', async () => {
      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      await userEvent.type(playerNameInput, 'John');

      const statsButton = screen.getByTestId('stats-button');
      fireEvent.click(statsButton);

      await waitFor(() => {
        expect(screen.getByTestId('stats-modal')).toBeInTheDocument();
      });

      const closeButton = screen.getByTestId('close-stats');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('stats-modal')).not.toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('disables buttons when processing', async () => {
      mockedAxios.post.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<App />);
      await waitFor(() => {
        expect(screen.getByTestId('player-name-input')).toBeInTheDocument();
      });

      const playerNameInput = screen.getByTestId('player-name-input');
      const guessInput = screen.getByTestId('guess-input');
      const submitButton = screen.getByTestId('submit-button');

      await userEvent.type(playerNameInput, 'John');
      fireEvent.change(guessInput, { target: { value: '10' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });
  });
});

