import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const steps = [
  { 
    id: 'router',
    name: 'Router Agent', 
    desc: 'Classifying modality...',
    icon: '🔀',
    activeDesc: 'Routing content to appropriate agent...',
    completedDesc: 'Content routed successfully',
    color: 'blue'
  },
  { 
    id: 'extractor',
    name: 'Content Extractor', 
    desc: 'Extracting content...',
    icon: '📄',
    activeDesc: 'Extracting text, images, or audio...',
    completedDesc: 'Content extracted successfully',
    color: 'purple'
  },
  { 
    id: 'classifier',
    name: 'Category Classifier', 
    desc: 'Assigning category...',
    icon: '🏷️',
    activeDesc: 'Categorizing content...',
    completedDesc: 'Category assigned successfully',
    color: 'pink'
  },
  { 
    id: 'labeler',
    name: 'Label Generator', 
    desc: 'Generating labels...',
    icon: '✨',
    activeDesc: 'Generating detailed labels...',
    completedDesc: 'Labels generated successfully',
    color: 'indigo'
  },
  { 
    id: 'quality',
    name: 'Quality Check', 
    desc: 'Validating quality...',
    icon: '✅',
    activeDesc: 'Performing quality checks...',
    completedDesc: 'Quality validated successfully',
    color: 'cyan'
  },
  { 
    id: 'output',
    name: 'JSON Output', 
    desc: 'Formatting output...',
    icon: '📊',
    activeDesc: 'Preparing final JSON output...',
    completedDesc: 'Output formatted successfully',
    color: 'emerald'
  },
];

const ProcessingPipeline = ({ autoStart = true, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('In Progress');
  const [stepStatuses, setStepStatuses] = useState(
    steps.map(() => 'pending')
  );
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    if (!autoStart) return;

    const stepDuration = 1500; // 1.5 seconds per step
    const progressInterval = 50; // Update progress every 50ms
    let progressTimer = null;
    let stepTimer = null;

    const startStep = (stepIndex) => {
      if (stepIndex >= steps.length) {
        // All steps completed
        setStatus('Completed');
        setIsCompleted(true);
        setProgress(100);
        if (onComplete) {
          setTimeout(() => onComplete(), 500);
        }
        return;
      }

      // Set current step to active
      setStepStatuses(prev => {
        const newStatuses = [...prev];
        newStatuses[stepIndex] = 'active';
        return newStatuses;
      });
      setCurrentStep(stepIndex);

      // Calculate target progress for this step
      const targetProgress = ((stepIndex + 1) / steps.length) * 100;
      const startProgress = (stepIndex / steps.length) * 100;
      const progressIncrement = (targetProgress - startProgress) / (stepDuration / progressInterval);

      let currentProgress = startProgress;

      // Update progress smoothly
      progressTimer = setInterval(() => {
        currentProgress += progressIncrement;
        if (currentProgress >= targetProgress) {
          currentProgress = targetProgress;
          clearInterval(progressTimer);
        }
        setProgress(currentProgress);
      }, progressInterval);

      // Complete step after duration
      stepTimer = setTimeout(() => {
        setStepStatuses(prev => {
          const newStatuses = [...prev];
          newStatuses[stepIndex] = 'completed';
          return newStatuses;
        });
        
        // Move to next step
        setTimeout(() => {
          startStep(stepIndex + 1);
        }, 200);
      }, stepDuration);
    };

    // Start the pipeline
    startStep(0);

    // Cleanup
    return () => {
      if (progressTimer) clearInterval(progressTimer);
      if (stepTimer) clearTimeout(stepTimer);
    };
  }, [autoStart, onComplete]);

  const getStepStatus = (index) => {
    if (index < currentStep) return 'completed';
    if (index === currentStep) return stepStatuses[index];
    return 'pending';
  };

  const getStepDescription = (step, index) => {
    const status = getStepStatus(index);
    if (status === 'completed') return step.completedDesc;
    if (status === 'active') return step.activeDesc;
    return step.desc;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="w-full max-w-4xl mx-auto p-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl border border-slate-700/50"
    >
      {/* Header with Status Badge */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex justify-between items-center mb-6"
      >
        <motion.h2
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="text-3xl font-bold text-white"
        >
          Processing Pipeline
        </motion.h2>
        <motion.div
          initial={{ scale: 0.8, opacity: 0, rotate: -10 }}
          animate={{ scale: 1, opacity: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 200, damping: 15 }}
          className={`px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2 ${
            isCompleted
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
          }`}
        >
          {isCompleted ? (
            <>
              <motion.span
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: [0, 1.3, 1], rotate: 0 }}
                transition={{ 
                  duration: 0.6,
                  type: "spring",
                  stiffness: 200
                }}
              >
                ✅
              </motion.span>
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                {status}
              </motion.span>
            </>
          ) : (
            <>
              <motion.div
                className="w-2 h-2 bg-blue-400 rounded-full"
                animate={{ 
                  opacity: [1, 0.3, 1],
                  scale: [1, 1.2, 1]
                }}
                transition={{ 
                  duration: 1.5, 
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
              {status}
            </>
          )}
        </motion.div>
      </motion.div>

      {/* Progress Bar */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mb-8"
      >
        <div className="flex justify-between items-center mb-2">
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-sm text-slate-400"
          >
            Overall Progress
          </motion.span>
          <motion.span
            key={progress}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ 
              scale: [1, 1.1, 1],
              opacity: 1
            }}
            transition={{ 
              duration: 0.3,
              type: "spring",
              stiffness: 300
            }}
            className="text-lg font-bold text-white"
          >
            {Math.round(progress)}%
          </motion.span>
        </div>
        <div className="w-full h-4 bg-slate-700/50 rounded-full overflow-hidden relative shadow-inner">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full relative overflow-hidden"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ 
              type: "spring",
              stiffness: 100,
              damping: 30,
              duration: 0.5
            }}
          >
            {/* Shimmer effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"
              animate={{
                x: ['-100%', '200%'],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'linear',
              }}
            />
            {/* Glow effect */}
            <motion.div
              className="absolute inset-0 bg-white/20 blur-sm"
              animate={{
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
          </motion.div>
        </div>
      </motion.div>

      {/* Steps */}
      <div className="space-y-4">
        <AnimatePresence mode="wait">
          {steps.map((step, index) => {
            const status = getStepStatus(index);
            const isActive = status === 'active';
            const isCompleted = status === 'completed';
            const isPending = status === 'pending';

            const colorClasses = {
              blue: 'from-blue-500/10 to-purple-500/10 border-blue-500/50 shadow-blue-500/20',
              purple: 'from-purple-500/10 to-pink-500/10 border-purple-500/50 shadow-purple-500/20',
              pink: 'from-pink-500/10 to-rose-500/10 border-pink-500/50 shadow-pink-500/20',
              indigo: 'from-indigo-500/10 to-purple-500/10 border-indigo-500/50 shadow-indigo-500/20',
              cyan: 'from-cyan-500/10 to-blue-500/10 border-cyan-500/50 shadow-cyan-500/20',
              emerald: 'from-emerald-500/10 to-green-500/10 border-emerald-500/50 shadow-emerald-500/20',
            };

            return (
              <motion.div
                key={`${step.id}-${status}`}
                initial={{ 
                  opacity: 0, 
                  x: -50,
                  scale: 0.95
                }}
                animate={{ 
                  opacity: 1, 
                  x: 0,
                  scale: 1,
                  ...(isActive && {
                    scale: [1, 1.01, 1],
                    y: [0, -2, 0],
                  }),
                  ...(isCompleted && {
                    scale: 1,
                  })
                }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ 
                  delay: index * 0.15,
                  type: "spring",
                  stiffness: 100,
                  damping: 15,
                  ...(isActive && {
                    scale: { duration: 2, repeat: Infinity },
                    y: { duration: 2, repeat: Infinity }
                  })
                }}
                whileHover={{ 
                  scale: 1.02,
                  x: 4,
                  transition: { duration: 0.2 }
                }}
                className={`relative p-5 rounded-xl border transition-all duration-300 ${
                  isActive
                    ? `bg-gradient-to-r ${colorClasses[step.color]} shadow-lg`
                    : isCompleted
                    ? 'bg-gradient-to-r from-green-500/10 to-emerald-500/10 border-green-500/30 shadow-md'
                    : 'bg-slate-800/50 border-slate-700/50'
                } hover:border-slate-600/70 hover:shadow-lg`}
              >
                <div className="flex items-center gap-4">
                  {/* Icon */}
                  <motion.div
                    key={`icon-${step.id}-${status}`}
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ 
                      scale: isActive ? [1, 1.2, 1] : isCompleted ? 1 : 1, 
                      rotate: isActive ? [0, 15, -15, 0] : 0,
                    }}
                    transition={{
                      scale: { 
                        duration: isActive ? 1.5 : 0.5, 
                        repeat: isActive ? Infinity : 0,
                        type: "spring",
                        stiffness: 200
                      },
                      rotate: { 
                        duration: 2, 
                        repeat: isActive ? Infinity : 0,
                        ease: "easeInOut"
                      },
                    }}
                    className={`w-14 h-14 rounded-lg flex items-center justify-center text-2xl transition-all ${
                      isActive
                        ? 'bg-blue-500/20 ring-2 ring-blue-500/50 ring-offset-2 ring-offset-slate-800 shadow-lg shadow-blue-500/30'
                        : isCompleted
                        ? 'bg-green-500/20 ring-2 ring-green-500/30'
                        : 'bg-slate-700/50'
                    }`}
                  >
                    <motion.span
                      key={`icon-span-${step.id}-${status}`}
                      animate={isActive ? {
                        filter: ['brightness(1)', 'brightness(1.5)', 'brightness(1)'],
                        scale: [1, 1.1, 1],
                      } : isCompleted ? {
                        scale: [1, 1.05, 1],
                      } : {}}
                      transition={{
                        duration: 1.5,
                        repeat: isActive ? Infinity : 0,
                        ease: "easeInOut"
                      }}
                    >
                      {step.icon}
                    </motion.span>
                  </motion.div>

                  {/* Content */}
                  <div className="flex-1">
                    <motion.h3
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.15 + 0.1 }}
                      className="text-lg font-semibold text-white mb-1"
                    >
                      {step.name}
                    </motion.h3>
                    <motion.p
                      key={getStepDescription(step, index)}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ 
                        opacity: 1, 
                        y: 0,
                        color: isActive 
                          ? 'rgb(147, 197, 253)' 
                          : isCompleted 
                          ? 'rgb(134, 239, 172)' 
                          : 'rgb(148, 163, 184)'
                      }}
                      transition={{ 
                        duration: 0.4,
                        type: "spring",
                        stiffness: 200
                      }}
                      className={`text-sm ${
                        isActive
                          ? 'text-blue-300'
                          : isCompleted
                          ? 'text-green-300'
                          : 'text-slate-400'
                      }`}
                    >
                      {getStepDescription(step, index)}
                    </motion.p>
                  </div>

                  {/* Status Indicator */}
                  <div className="flex-shrink-0">
                    {isPending && (
                      <motion.div
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: index * 0.15 + 0.2 }}
                        className="w-8 h-8 rounded-full border-2 border-slate-600"
                      />
                    )}
                    {isActive && (
                      <motion.div
                        key={`spinner-${step.id}`}
                        initial={{ scale: 0, rotate: -180, opacity: 0 }}
                        animate={{ 
                          scale: 1, 
                          rotate: 0,
                          opacity: 1
                        }}
                        transition={{
                          type: "spring",
                          stiffness: 200,
                          damping: 15
                        }}
                        className="w-8 h-8 rounded-full border-2 border-blue-500 relative"
                      >
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{
                            duration: 1,
                            repeat: Infinity,
                            ease: 'linear',
                          }}
                          className="w-full h-full absolute inset-0"
                        >
                          <motion.div
                            className="absolute inset-0 rounded-full border-2 border-blue-500 border-t-transparent"
                            animate={{ rotate: 360 }}
                            transition={{
                              duration: 0.8,
                              repeat: Infinity,
                              ease: 'linear',
                            }}
                          />
                        </motion.div>
                        {/* Pulsing glow */}
                        <motion.div
                          className="absolute inset-0 rounded-full bg-blue-500/30 -z-10"
                          animate={{
                            scale: [1, 1.5, 1],
                            opacity: [0.6, 0, 0.6],
                          }}
                          transition={{
                            duration: 1.5,
                            repeat: Infinity,
                            ease: 'easeInOut',
                          }}
                        />
                        {/* Inner dot */}
                        <motion.div
                          className="absolute inset-2 rounded-full bg-blue-500"
                          animate={{
                            scale: [1, 1.2, 1],
                            opacity: [1, 0.7, 1],
                          }}
                          transition={{
                            duration: 1,
                            repeat: Infinity,
                            ease: 'easeInOut',
                          }}
                        />
                      </motion.div>
                    )}
                    {isCompleted && (
                      <motion.div
                        initial={{ scale: 0, rotate: -180 }}
                        animate={{ 
                          scale: [0, 1.2, 1],
                          rotate: 0
                        }}
                        transition={{ 
                          duration: 0.6,
                          type: "spring",
                          stiffness: 200
                        }}
                        className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center shadow-lg shadow-green-500/50"
                      >
                        <motion.svg
                          initial={{ pathLength: 0, opacity: 0 }}
                          animate={{ 
                            pathLength: 1,
                            opacity: 1
                          }}
                          transition={{ 
                            duration: 0.5,
                            delay: 0.2,
                            ease: "easeOut"
                          }}
                          className="w-5 h-5 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <motion.path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={3}
                            d="M5 13l4 4L19 7"
                            initial={{ pathLength: 0 }}
                            animate={{ pathLength: 1 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                          />
                        </motion.svg>
                        {/* Completion pulse */}
                        <motion.div
                          className="absolute inset-0 rounded-full bg-green-400"
                          initial={{ scale: 1, opacity: 0.8 }}
                          animate={{
                            scale: [1, 1.5, 1.5],
                            opacity: [0.8, 0, 0],
                          }}
                          transition={{
                            duration: 0.6,
                            ease: "easeOut"
                          }}
                        />
                      </motion.div>
                    )}
                  </div>
                </div>

                {/* Active Glow Effect */}
                <AnimatePresence>
                  {isActive && (
                    <>
                      <motion.div
                        key={`sweep-${step.id}`}
                        initial={{ x: '-100%' }}
                        animate={{
                          x: ['-100%', '200%'],
                        }}
                        exit={{ opacity: 0 }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: 'linear',
                        }}
                        className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-blue-500/30 to-transparent"
                        style={{ pointerEvents: 'none' }}
                      />
                      {/* Pulsing border glow */}
                      <motion.div
                        key={`border-glow-${step.id}`}
                        initial={{ opacity: 0 }}
                        animate={{
                          opacity: [0.4, 0.8, 0.4],
                          scale: [1, 1.02, 1],
                        }}
                        exit={{ opacity: 0 }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: 'easeInOut',
                        }}
                        className="absolute inset-0 rounded-xl border-2 border-blue-500/60"
                        style={{ pointerEvents: 'none' }}
                      />
                      {/* Radial glow */}
                      <motion.div
                        key={`radial-glow-${step.id}`}
                        className="absolute inset-0 rounded-xl bg-blue-500/10"
                        animate={{
                          opacity: [0.2, 0.4, 0.2],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          ease: 'easeInOut',
                        }}
                        style={{ pointerEvents: 'none' }}
                      />
                    </>
                  )}
                </AnimatePresence>
                
                {/* Completed shimmer */}
                {isCompleted && (
                  <motion.div
                    className="absolute inset-0 rounded-xl bg-gradient-to-r from-green-500/0 via-green-500/10 to-green-500/0"
                    initial={{ x: '-100%' }}
                    animate={{ x: '100%' }}
                    transition={{
                      duration: 1,
                      ease: 'easeOut',
                    }}
                    style={{ pointerEvents: 'none' }}
                  />
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Completion Message */}
      <AnimatePresence>
        {isCompleted && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{
              type: "spring",
              stiffness: 100,
              damping: 15
            }}
            className="mt-6 p-8 bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-xl text-center relative overflow-hidden"
          >
            {/* Background particles */}
            <motion.div
              className="absolute inset-0"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-2 h-2 bg-green-400 rounded-full"
                  initial={{
                    x: '50%',
                    y: '50%',
                    scale: 0,
                  }}
                  animate={{
                    x: `${50 + (Math.random() - 0.5) * 100}%`,
                    y: `${50 + (Math.random() - 0.5) * 100}%`,
                    scale: [0, 1, 0],
                    opacity: [0, 1, 0],
                  }}
                  transition={{
                    duration: 2,
                    delay: i * 0.2,
                    repeat: Infinity,
                    ease: 'easeOut',
                  }}
                />
              ))}
            </motion.div>
            
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ 
                scale: [0, 1.3, 1],
                rotate: 0
              }}
              transition={{ 
                duration: 0.8,
                type: "spring",
                stiffness: 200,
                delay: 0.2
              }}
              className="text-6xl mb-4 relative z-10"
            >
              <motion.span
                animate={{
                  rotate: [0, 10, -10, 0],
                  scale: [1, 1.1, 1],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                ✅
              </motion.span>
            </motion.div>
            
            <motion.h3
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="text-3xl font-bold text-white mb-3 relative z-10"
            >
              Pipeline Completed
            </motion.h3>
            
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="text-green-300 text-lg relative z-10"
            >
              All processing stages completed successfully
            </motion.p>
            
            {/* Success glow */}
            <motion.div
              className="absolute inset-0 bg-green-400/20 rounded-xl"
              animate={{
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ProcessingPipeline;

