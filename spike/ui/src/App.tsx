import React, { useState } from 'react';

export default function App() {
  const [story, setStory] = useState('');
  const [feature, setFeature] = useState('');

  const handleGenerate = () => {
    if (!story) return;
    setFeature(`Feature: ${story}\n\n  Scenario: Primary flow\n    Given system is ready\n    When user performs action\n    Then expected result occurs`);
  };

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Antinode Norma BDD - UI Spike</h1>
      <p>Proof of concept for Track C Web Interface</p>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>User Story Input:</label>
        <textarea
          rows={4}
          style={{ width: '100%', padding: '0.5rem' }}
          placeholder="As a user, I want to log in..."
          value={story}
          onChange={(e) => setStory(e.target.value)}
        />
      </div>

      <button
        onClick={handleGenerate}
        style={{ padding: '0.5rem 1rem', background: '#0066cc', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
      >
        Generate Feature
      </button>

      {feature && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Generated Feature Output:</h2>
          <pre style={{ background: '#f4f4f4', padding: '1rem', borderRadius: '4px', overflowX: 'auto' }}>
            {feature}
          </pre>
        </div>
      )}
    </div>
  );
}
