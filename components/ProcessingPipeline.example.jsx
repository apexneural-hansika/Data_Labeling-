import React from 'react';
import ProcessingPipeline from './ProcessingPipeline';

// Example usage
function App() {
  const handleComplete = () => {
    console.log('Pipeline completed!');
    // Handle completion logic here
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <ProcessingPipeline 
        autoStart={true} 
        onComplete={handleComplete}
      />
    </div>
  );
}

export default App;


