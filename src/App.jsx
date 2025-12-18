import React from 'react';
import ProcessingPipeline from '../components/ProcessingPipeline';

function App() {
  const handleComplete = () => {
    console.log('Pipeline completed!');
    // You can add navigation, show results, etc. here
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8 text-center">
          NexusAI Processing Pipeline
        </h1>
        <ProcessingPipeline 
          autoStart={true} 
          onComplete={handleComplete}
        />
      </div>
    </div>
  );
}

export default App;


