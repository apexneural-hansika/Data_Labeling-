# ProcessingPipeline Component

An interactive React component that visually animates each stage of the labeling workflow with smooth transitions and real-time progress tracking.

## Features

- ✅ Sequential stage animations (one after another)
- ✅ Dynamic progress bar (0-100%)
- ✅ Circular progress indicators and glowing checkmarks
- ✅ Status badges ("In Progress" → "Completed")
- ✅ Dark modern UI with card layouts
- ✅ Smooth hover effects and transitions
- ✅ Auto-start simulation on page load
- ✅ Completion message with animated success checkmark

## Installation

### 1. Install Dependencies

```bash
npm install
```

Or with yarn:

```bash
yarn install
```

### 2. Setup Tailwind CSS (if not already configured)

Create `tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Create `postcss.config.js`:

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

Add to your main CSS file:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 3. Setup Vite (if using Vite)

Create `vite.config.js`:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```

## Usage

### Basic Usage

```jsx
import React from 'react';
import ProcessingPipeline from './components/ProcessingPipeline';

function App() {
  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <ProcessingPipeline autoStart={true} />
    </div>
  );
}

export default App;
```

### With Completion Callback

```jsx
import React from 'react';
import ProcessingPipeline from './components/ProcessingPipeline';

function App() {
  const handleComplete = () => {
    console.log('Pipeline completed!');
    // Navigate to results page, show success message, etc.
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
```

### Manual Control

```jsx
import React, { useState } from 'react';
import ProcessingPipeline from './components/ProcessingPipeline';

function App() {
  const [startPipeline, setStartPipeline] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <button 
        onClick={() => setStartPipeline(true)}
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        Start Processing
      </button>
      
      <ProcessingPipeline autoStart={startPipeline} />
    </div>
  );
}

export default App;
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `autoStart` | `boolean` | `true` | Automatically start the pipeline animation on mount |
| `onComplete` | `function` | `undefined` | Callback function called when all stages complete |

## Customization

### Changing Step Duration

Edit the `stepDuration` variable in `ProcessingPipeline.jsx`:

```jsx
const stepDuration = 1500; // Change to desired milliseconds (default: 1500ms = 1.5s)
```

### Customizing Steps

Modify the `steps` array in `ProcessingPipeline.jsx`:

```jsx
const steps = [
  { 
    id: 'router',
    name: 'Router Agent', 
    desc: 'Classifying modality...',
    icon: '🔀',
    activeDesc: 'Routing content...',
    completedDesc: 'Content routed successfully'
  },
  // Add more steps...
];
```

### Styling

The component uses Tailwind CSS classes. You can customize colors by modifying the className strings:

- Background: `bg-slate-900`, `bg-slate-800`
- Active state: `bg-blue-500`, `text-blue-400`
- Completed state: `bg-green-500`, `text-green-400`
- Progress bar: `from-blue-500 via-purple-500 to-pink-500`

## Integration with Flask Backend

To integrate with your existing Flask backend:

```jsx
import React, { useState, useEffect } from 'react';
import ProcessingPipeline from './components/ProcessingPipeline';

function LabelingPage() {
  const [taskId, setTaskId] = useState(null);
  const [pipelineComplete, setPipelineComplete] = useState(false);

  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    if (result.task_id) {
      setTaskId(result.task_id);
      // Start polling for actual progress
      pollTaskStatus(result.task_id);
    }
  };

  const pollTaskStatus = async (taskId) => {
    const interval = setInterval(async () => {
      const response = await fetch(`/api/task/${taskId}`);
      const task = await response.json();
      
      // Update pipeline based on actual task status
      if (task.status === 'completed') {
        clearInterval(interval);
        setPipelineComplete(true);
      }
    }, 1000);
  };

  return (
    <div>
      {/* File upload form */}
      <ProcessingPipeline 
        autoStart={!!taskId}
        onComplete={() => {
          setPipelineComplete(true);
          // Show results
        }}
      />
    </div>
  );
}
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

MIT


