import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { ArrowLeft, CheckCircle, AlertTriangle, Wrench, Clock, Image as ImageIcon, Camera } from 'lucide-react';
import dynamic from 'next/dynamic';

// Dynamically import ARView to avoid SSR issues with camera API
const ARView = dynamic(() => import('../../components/ARView'), { ssr: false });

interface TutorialStep {
  step: number;
  action: string;
  description?: string;
  image?: string;
  video_timestamp?: string;
  warning?: string;
  tools?: string[];
}

interface Tutorial {
  id: number;
  title: string;
  brand: string;
  model: string;
  issue_type: string;
  difficulty: string;
  source: string;
  steps: TutorialStep[];
  tools: string[];
  warnings: string[];
  images: string[];
  estimated_time?: string;
  risk_level?: string;
}

export default function TutorialDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [arMode, setArMode] = useState(false);

  useEffect(() => {
    if (id) {
      fetchTutorial();
    }
  }, [id]);

  const fetchTutorial = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/v2/tutorial/${id}`);
      
      if (!response.ok) {
        throw new Error('Tutorial not found');
      }
      
      const data = await response.json();
      // The API returns {tutorial: {...}}
      if (data.tutorial) {
        setTutorial(data.tutorial);
      } else {
        throw new Error('Invalid tutorial data');
      }
    } catch (error) {
      console.error('Error fetching tutorial:', error);
      alert('Failed to load tutorial. It may not exist.');
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy': return 'success';
      case 'medium': return 'warning';
      case 'hard': return 'danger';
      default: return 'default';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case 'safe': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // AR Mode Full Screen View
  if (arMode && tutorial) {
    // Determine category from tutorial data
    const category = tutorial.brand?.toLowerCase().includes('phone') || 
                     tutorial.model?.toLowerCase().includes('phone') ||
                     tutorial.issue_type?.toLowerCase().includes('phone') ? 'phone' :
                     tutorial.brand?.toLowerCase().includes('tablet') ||
                     tutorial.model?.toLowerCase().includes('tablet') ? 'tablet' : 'laptop';

    return (
      <ARView
        currentStep={currentStep}
        totalSteps={tutorial.steps.length}
        stepTitle={tutorial.steps[currentStep]?.action || ''}
        stepDescription={tutorial.steps[currentStep]?.description || tutorial.steps[currentStep]?.action || ''}
        stepImage={tutorial.steps[currentStep]?.image}
        tutorialId={tutorial.id}
        category={category}
        onStepChange={setCurrentStep}
        onClose={() => setArMode(false)}
      />
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-neutral-600">Loading tutorial...</p>
        </div>
      </div>
    );
  }

  if (!tutorial) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Tutorial Not Found</h2>
            <p className="text-neutral-600 mb-4">The tutorial you're looking for doesn't exist.</p>
            <Button onClick={() => router.push('/guides')}>Browse Guides</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
      {/* Compact Header */}
      <header className="border-b border-neutral-200 bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="sm" onClick={() => router.back()}>
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back
            </Button>
            <div className="flex items-center gap-3">
              <Button 
                variant="primary" 
                size="sm"
                onClick={() => setArMode(true)}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <Camera className="w-4 h-4 mr-2" />
                Start AR Mode
              </Button>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Badge variant={getDifficultyColor(tutorial.difficulty)}>
                {tutorial.difficulty || 'Medium'}
              </Badge>
              <Badge variant="default">{tutorial.source || 'iFixit'}</Badge>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Two-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          
          {/* Left Column: Tutorial Info & Tools (1 column) */}
          <div className="lg:col-span-1 space-y-4">
            {/* Tutorial Header */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{tutorial.title}</CardTitle>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  <Badge variant="default" className="text-xs capitalize">
                    {tutorial.brand} {tutorial.model}
                  </Badge>
                  <Badge variant="default" className="text-xs capitalize">
                    {tutorial.issue_type}
                  </Badge>
                </div>
              </CardHeader>
            </Card>

            {/* Tools Required */}
            {tutorial.tools && tutorial.tools.length > 0 && (
              <Card className="shadow-sm">
                <CardContent className="pt-4">
                  <h3 className="font-semibold text-sm text-blue-900 mb-2 flex items-center gap-2">
                    <Wrench className="w-4 h-4" />
                    Tools Required
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {tutorial.tools.map((tool, idx) => (
                      <Badge key={idx} variant="default" className="text-xs">{tool}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Warnings */}
            {tutorial.warnings && tutorial.warnings.length > 0 && (
              <Card className="shadow-sm border-yellow-300">
                <CardContent className="pt-4">
                  <h3 className="font-semibold text-sm text-yellow-900 mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Warnings
                  </h3>
                  <ul className="space-y-1 text-xs text-yellow-800">
                    {tutorial.warnings.map((warning, idx) => (
                      <li key={idx}>• {warning}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Step Navigation Vertical */}
            <Card className="shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">All Steps</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-5 sm:grid-cols-6 lg:grid-cols-4 gap-2">
                  {tutorial.steps.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => setCurrentStep(idx)}
                      className={`
                        w-10 h-10 rounded-lg font-semibold text-sm transition-all
                        ${idx === currentStep 
                          ? 'bg-primary-600 text-white shadow-md ring-2 ring-primary-300' 
                          : idx < currentStep
                          ? 'bg-green-500 text-white'
                          : 'bg-neutral-200 text-neutral-600 hover:bg-neutral-300'
                        }
                      `}
                    >
                      {idx < currentStep ? '✓' : idx + 1}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Current Step (2 columns) */}
          <div className="lg:col-span-2">
            <Card className="shadow-md">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-primary-600 text-white flex items-center justify-center text-lg font-bold shadow">
                      {currentStep + 1}
                    </div>
                    <div>
                      <div className="text-xs text-neutral-500 uppercase tracking-wide">
                        Step {currentStep + 1} of {tutorial.steps.length}
                      </div>
                      <h3 className="text-base font-bold text-neutral-900">
                        {tutorial.steps[currentStep]?.action}
                      </h3>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {tutorial.steps[currentStep] && (
                  <>
                    {/* Step Image - Scaled down 4:3 Ratio */}
                    <div className="relative w-full max-w-md aspect-[4/3] bg-gradient-to-br from-blue-50 via-white to-blue-50 rounded-lg overflow-hidden border border-blue-200">
                      {tutorial.steps[currentStep].image ? (
                        <img
                          src={tutorial.steps[currentStep].image}
                          alt={`Step ${currentStep + 1}`}
                          className="w-full h-full object-contain bg-white"
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full text-blue-500 text-sm">
                          <span>Visual guide coming in AR mode</span>
                        </div>
                      )}
                    </div>

                    {/* Step Instructions - Compact */}
                    <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                      <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
                        {tutorial.steps[currentStep].description || tutorial.steps[currentStep].action}
                      </p>
                    </div>

                    {/* Navigation Buttons - Compact */}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                        disabled={currentStep === 0}
                        className="flex-1"
                      >
                        ← Previous
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setCurrentStep(Math.min(tutorial.steps.length - 1, currentStep + 1))}
                        disabled={currentStep === tutorial.steps.length - 1}
                        className="flex-1"
                      >
                        {currentStep === tutorial.steps.length - 1 ? 'Complete ✓' : 'Next →'}
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
