import React, { useEffect, useRef } from 'react';

const ResultsPanel = ({ results }) => {
  const textRef = useRef();

  useEffect(() => {
    if (textRef.current) {
      textRef.current.scrollTop = textRef.current.scrollHeight;
    }
  }, [results]);

  return (
    <div className="results-panel">
      <h3 className="results-title">Results</h3>
      <div className="results-content" ref={textRef}>
        {results.length === 0 ? (
          <p className="no-results">No results yet. Make a guess to get started!</p>
        ) : (
          results.map((result, index) => (
            <pre key={index} className="result-text">
              {result}
            </pre>
          ))
        )}
      </div>
    </div>
  );
};

export default ResultsPanel;