import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';

interface RepairStep {
  id: number;
  action: string;
  tools: string[];
  risk: string;
  warnings: string[];
  image: string;
}

export default function RepairPage() {
  const router = useRouter();
  const { device, issue } = router.query;

  const [currentStep, setCurrentStep] = useState(0);
  const [showOverlay, setShowOverlay] = useState(true);

  const steps: RepairStep[] = [
    {
      id: 1,
      action: 'Disconnect AC adapter and power off the device',
      tools: [],
      risk: 'safe',
      warnings: ['Ensure device is completely powered off'],
      image: '/placeholder-step1.jpg',
    },
    {
      id: 2,
      action: 'Remove the bottom cover screws',
      tools: ['Torx-5'],
      risk: 'safe',
      warnings: ['Keep screws organized by location'],
      image: '/placeholder-step2.jpg',
    },
    {
      id: 3,
      action: 'Disconnect the battery connector',
      tools: ['Plastic Spudger'],
      risk: 'medium',
      warnings: ['Avoid touching other components', 'Use plastic tool only'],
      image: '/placeholder-step3.jpg',
    },
  ];

  const currentStepData = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      router.push('/complete');
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-900">
      {/* Header */}
      <header className="border-b border-neutral-800 bg-neutral-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => router.back()} className="text-neutral-400 hover:text-white">
              ← Exit Repair
            </Button>
            <div className="text-center">
              <h1 className="text-lg font-semibold text-white">Repair Guide</h1>
              {device && (
                <p className="text-sm text-neutral-400 capitalize">
                  {String(device).replace(/_/g, ' ')}
                </p>
              )}
            </div>
            <Button
              variant="ghost"
              onClick={() => setShowOverlay(!showOverlay)}
              className="text-neutral-400 hover:text-white"
            >
              {showOverlay ? '👁️ Hide' : '👁️ Show'}
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main AR View */}
          <div className="lg:col-span-2">
            <Card className="bg-neutral-800 border-neutral-700">
              <CardContent className="p-0">
                {/* Image with AR Overlay */}
                <div className="relative aspect-video bg-neutral-900 rounded-t-xl overflow-hidden">
                  {/* Placeholder for actual image */}
                  <div className="absolute inset-0 flex items-center justify-center text-neutral-600">
                    <div className="text-center">
                      <div className="text-6xl mb-4">📷</div>
                      <p>Device Image with AR Overlay</p>
                      <p className="text-sm text-neutral-500 mt-2">{currentStepData.image}</p>
                    </div>
                  </div>

                  {/* AR Overlay Elements */}
                  {showOverlay && (
                    <>
                      {/* Example overlay markers */}
                      <div className="absolute top-1/3 left-1/4 w-12 h-12 border-4 border-yellow-400 rounded-full animate-pulse-subtle flex items-center justify-center text-yellow-400 font-bold text-xl">
                        1
                      </div>
                      <div className="absolute top-1/2 right-1/3 w-12 h-12 border-4 border-yellow-400 rounded-full animate-pulse-subtle flex items-center justify-center text-yellow-400 font-bold text-xl">
                        2
                      </div>
                    </>
                  )}
                </div>

                {/* Progress Bar */}
                <div className="p-4 border-t border-neutral-700">
                  <Progress value={progress} size="md" showLabel />
                  <p className="text-xs text-neutral-400 mt-2 text-center">
                    Step {currentStep + 1} of {steps.length}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Navigation Controls */}
            <div className="grid grid-cols-3 gap-4 mt-4">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className="bg-neutral-800 border-neutral-700 text-white hover:bg-neutral-700"
              >
                ← Previous
              </Button>
              <Button
                variant="secondary"
                onClick={() => {/* TTS */}}
                className="bg-neutral-800 border-neutral-700 text-white hover:bg-neutral-700"
              >
                🔊 Repeat
              </Button>
              <Button
                onClick={handleNext}
                className="bg-white text-neutral-900 hover:bg-neutral-100"
              >
                {currentStep === steps.length - 1 ? 'Finish' : 'Next →'}
              </Button>
            </div>
          </div>

          {/* Step Instructions Panel */}
          <div className="space-y-4">
            {/* Current Step Card */}
            <Card className="bg-neutral-800 border-neutral-700">
              <CardHeader>
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant={currentStepData.risk === 'safe' ? 'success' : 'warning'} className="capitalize">
                    {currentStepData.risk}
                  </Badge>
                  <span className="text-sm text-neutral-400">Step {currentStepData.id}</span>
                </div>
                <CardTitle className="text-white text-xl">{currentStepData.action}</CardTitle>
              </CardHeader>
              <CardContent>
                {/* Tools Required */}
                {currentStepData.tools.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-neutral-300 mb-2">Tools Needed:</h4>
                    <div className="flex flex-wrap gap-2">
                      {currentStepData.tools.map((tool) => (
                        <Badge key={tool} variant="default" className="bg-neutral-700 text-neutral-200">
                          🔧 {tool}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {currentStepData.warnings.length > 0 && (
                  <div className="bg-warning-900/20 border border-warning-600 rounded-lg p-3">
                    <h4 className="text-sm font-semibold text-warning-400 mb-2 flex items-center gap-2">
                      ⚠️ Important
                    </h4>
                    <ul className="text-sm text-warning-200 space-y-1">
                      {currentStepData.warnings.map((warning, index) => (
                        <li key={index}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* All Steps List */}
            <Card className="bg-neutral-800 border-neutral-700">
              <CardHeader>
                <CardTitle className="text-white text-sm">All Steps</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {steps.map((step, index) => (
                    <button
                      key={step.id}
                      onClick={() => setCurrentStep(index)}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        index === currentStep
                          ? 'bg-neutral-700 border-2 border-white'
                          : index < currentStep
                          ? 'bg-neutral-900 border border-success-600 text-neutral-400'
                          : 'bg-neutral-900 border border-neutral-700 text-neutral-500'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          index < currentStep ? 'bg-success-600 text-white' : 'bg-neutral-700 text-neutral-300'
                        }`}>
                          {index < currentStep ? '✓' : index + 1}
                        </div>
                        <div className="flex-1">
                          <p className={`text-sm font-medium ${
                            index === currentStep ? 'text-white' : ''
                          }`}>
                            {step.action}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
