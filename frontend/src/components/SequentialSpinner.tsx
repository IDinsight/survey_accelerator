import React, { useState, useEffect } from 'react';
import './Spinner.css';

interface SequentialSpinnerProps {
  onComplete: () => void;
  resultsReady: boolean;
}

interface CustomCSSProperties extends React.CSSProperties {
  [key: string]: string | number | undefined;
}

const SequentialSpinner: React.FC<SequentialSpinnerProps> = ({ onComplete, resultsReady }) => {
  const [spinnerStep, setSpinnerStep] = useState<number>(1);
  const [spinnerLoopCount, setSpinnerLoopCount] = useState<number>(0);

  // Constants (in seconds)
  const SPINNER1_TOTAL = 2.6; // Phase 1: 2 loops at 1.3s each
  const SPINNER2_TOTAL = 4;   // Phase 2: 2 loops at 2s each
  const SPINNER3_LOOP = 2;    // Phase 3: each loop now takes 2s (sped up)

  // Phase 1: Run spinner1 for exactly SPINNER1_TOTAL seconds.
  useEffect(() => {
    const timer1 = window.setTimeout(() => {
      setSpinnerStep(2);
    }, SPINNER1_TOTAL * 1000);
    return () => clearTimeout(timer1);
  }, []);

  // Phase 2: When spinnerStep becomes 2, run spinner2 for exactly SPINNER2_TOTAL seconds.
  useEffect(() => {
    if (spinnerStep === 2) {
      const timer2 = window.setTimeout(() => {
        setSpinnerStep(3);
      }, SPINNER2_TOTAL * 1000);
      return () => clearTimeout(timer2);
    }
  }, [spinnerStep]);

  // Phase 3: When spinnerStep is 3, run loops of spinner3 until resultsReady is true.
  useEffect(() => {
    if (spinnerStep === 3) {
      const timer3 = window.setTimeout(() => {
        if (resultsReady) {
          onComplete();
        } else {
          setSpinnerLoopCount((prev) => prev + 1);
        }
      }, SPINNER3_LOOP * 1000);
      return () => clearTimeout(timer3);
    }
  }, [spinnerStep, resultsReady, spinnerLoopCount, onComplete]);

  // Determine spinner class, inline style, and status text.
  let spinnerClass = '';
  let inlineStyle: CustomCSSProperties = {};
  let statusText = '';
  if (spinnerStep === 1) {
    spinnerClass = 'spinner1';
    inlineStyle = { '--spinner-duration': '1.3s' };
    statusText = "Searching surveys";
  } else if (spinnerStep === 2) {
    spinnerClass = 'spinner2';
    inlineStyle = { '--spinner-duration': '2s' };
    statusText = "Ranking results";
  } else if (spinnerStep === 3) {
    spinnerClass = 'spinner3';
    inlineStyle = { '--spinner-duration': '2s' }; // Faster animation now.
    statusText = "Generating match explanations and highlights";
  }

  return (
    <div style={{ width: '100%', textAlign: 'center' }}>
      <div style={{ display: 'inline-block', margin: '0 auto' }}>
        <div className={spinnerClass} style={inlineStyle}></div>
      </div>
      <div style={{ marginTop: '10px', fontWeight: 'bold', width: '100%', textAlign: 'center' }}>
        {statusText}
      </div>
    </div>
  );
};

export default SequentialSpinner;
