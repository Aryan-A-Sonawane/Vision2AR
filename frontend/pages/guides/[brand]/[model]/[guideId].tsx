import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Card, CardContent } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { Button } from '../../../../components/ui/Button';
import { 
  ArrowLeft, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  Download,
  Eye,
  Camera,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

// Mock guide detail data - will be replaced with API
const GUIDE_DETAILS: Record<string, any> = {
  'battery-replacement': {
    title: 'Battery Replacement',
    model: 'IdeaPad 5',
    brand: 'Lenovo',
    difficulty: 'Easy',
    time: '10-20 min',
    views: 15632,
    rating: 4.9,
    author: {
      name: 'OEM Service Manual',
      verified: true
    },
    tools: [
      { name: 'Phillips #0 Screwdriver', required: true },
      { name: 'Plastic Spudger', required: true },
      { name: 'Anti-static wrist strap', required: false }
    ],
    parts: [
      { name: 'Lenovo IdeaPad 5 Battery (L19M4PC0)', link: '#' }
    ],
    warnings: [
      'Disconnect all power sources before starting',
      'Handle battery carefully - do not puncture or damage',
      'Dispose of old battery properly at an e-waste facility'
    ],
    introduction: 'This guide will walk you through replacing the internal battery in your Lenovo IdeaPad 5. This repair is necessary when your battery no longer holds a charge or your laptop won\'t power on.',
    steps: [
      {
        number: 1,
        title: 'Power Off and Prepare',
        content: 'Shut down your laptop completely. Disconnect the power adapter and any external devices. Place the laptop on a clean, flat surface with the bottom facing up.',
        image: '/assets/lenovo/ideapad_5/step1_prepare.jpg',
        warnings: ['Ensure laptop is completely powered off'],
        tips: ['Use an anti-static mat if available']
      },
      {
        number: 2,
        title: 'Remove Bottom Cover Screws',
        content: 'Using a Phillips #0 screwdriver, remove the 8 screws securing the bottom cover. Keep the screws organized as they may be different lengths.',
        image: '/assets/lenovo/ideapad_5/step2_screws.jpg',
        warnings: [],
        tips: ['Place screws in a container to avoid losing them', 'Note screw positions - some may be different sizes']
      },
      {
        number: 3,
        title: 'Remove Bottom Cover',
        content: 'Insert a plastic spudger into the gap between the bottom cover and the chassis near the hinge. Gently pry around the perimeter to release the clips. Lift the cover away.',
        image: '/assets/lenovo/ideapad_5/step3_cover.jpg',
        warnings: ['Do not use excessive force - clips can break'],
        tips: ['Start from the hinge area where the gap is wider']
      },
      {
        number: 4,
        title: 'Disconnect Battery Cable',
        content: 'Locate the battery connector on the motherboard. Use your fingers or a spudger to gently lift the connector straight up from its socket. Do not pull on the wires.',
        image: '/assets/lenovo/ideapad_5/step4_disconnect.jpg',
        warnings: ['Pull connector, not wires', 'Ensure laptop is powered off'],
        tips: ['The connector lifts straight up - no need to rock it']
      },
      {
        number: 5,
        title: 'Remove Battery Screws',
        content: 'Remove the 4 Phillips screws securing the battery to the chassis.',
        image: '/assets/lenovo/ideapad_5/step5_battery_screws.jpg',
        warnings: [],
        tips: []
      },
      {
        number: 6,
        title: 'Remove Old Battery',
        content: 'Carefully lift the battery out of the chassis. Handle by the edges and avoid pressing on the battery cells.',
        image: '/assets/lenovo/ideapad_5/step6_remove.jpg',
        warnings: ['Do not puncture or bend battery', 'Dispose of properly'],
        tips: []
      },
      {
        number: 7,
        title: 'Install New Battery',
        content: 'Place the new battery into the chassis, aligning it with the screw holes. Secure with the 4 Phillips screws.',
        image: '/assets/lenovo/ideapad_5/step7_install.jpg',
        warnings: ['Ensure battery is oriented correctly'],
        tips: ['Do not overtighten screws']
      },
      {
        number: 8,
        title: 'Reconnect Battery Cable',
        content: 'Connect the battery cable to the motherboard by pressing the connector firmly into its socket until it clicks.',
        image: '/assets/lenovo/ideapad_5/step8_connect.jpg',
        warnings: [],
        tips: ['Ensure connector is fully seated']
      },
      {
        number: 9,
        title: 'Replace Bottom Cover',
        content: 'Align the bottom cover with the chassis and press around the perimeter to snap the clips into place. Replace all 8 screws.',
        image: '/assets/lenovo/ideapad_5/step9_reassemble.jpg',
        warnings: [],
        tips: ['Ensure all clips are engaged before tightening screws']
      },
      {
        number: 10,
        title: 'Test and Calibrate',
        content: 'Connect the power adapter and power on the laptop. Check that the battery is recognized in the system. For best results, fully charge and discharge the battery once to calibrate it.',
        image: '/assets/lenovo/ideapad_5/step10_test.jpg',
        warnings: [],
        tips: ['Allow full charge cycle for battery calibration']
      }
    ],
    sources: ['OEM Service Manual', 'iFixit'],
    relatedGuides: [
      { id: 'ssd-upgrade', title: 'SSD Upgrade', difficulty: 'Easy' },
      { id: 'ram-upgrade', title: 'RAM Upgrade', difficulty: 'Easy' }
    ]
  }
};

const DIFFICULTY_COLORS: Record<string, string> = {
  'Easy': 'bg-green-100 text-green-700 border-green-200',
  'Medium': 'bg-amber-100 text-amber-700 border-amber-200',
  'Hard': 'bg-red-100 text-red-700 border-red-200'
};

export default function GuideDetail() {
  const router = useRouter();
  const { brand, model, guideId } = router.query;
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([1]));
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const guide = GUIDE_DETAILS[guideId as string];

  if (!guide) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-neutral-600">Loading guide...</p>
        </div>
      </div>
    );
  }

  const toggleStep = (stepNumber: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepNumber)) {
      newExpanded.delete(stepNumber);
    } else {
      newExpanded.add(stepNumber);
    }
    setExpandedSteps(newExpanded);
  };

  const toggleComplete = (stepNumber: number) => {
    const newCompleted = new Set(completedSteps);
    if (newCompleted.has(stepNumber)) {
      newCompleted.delete(stepNumber);
    } else {
      newCompleted.add(stepNumber);
    }
    setCompletedSteps(newCompleted);
  };

  const startARView = () => {
    router.push(`/repair?device=${brand}_${model}&guide=${guideId}`);
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link 
            href={`/guides/${brand}/${model}`}
            className="inline-flex items-center text-neutral-600 hover:text-neutral-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to {guide.brand} {guide.model} guides
          </Link>

          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-neutral-900 mb-2">
                {guide.title}
              </h1>
              <p className="text-neutral-600">
                {guide.brand} {guide.model}
              </p>
            </div>
            <Badge className={DIFFICULTY_COLORS[guide.difficulty]}>
              {guide.difficulty}
            </Badge>
          </div>

          {/* Meta Info */}
          <div className="flex items-center gap-6 text-sm text-neutral-600 mb-6">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {guide.time}
            </span>
            <span className="flex items-center gap-1">
              <Eye className="w-4 h-4" />
              {guide.views.toLocaleString()} views
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="w-4 h-4" />
              {guide.steps.length} steps
            </span>
          </div>

          {/* AR View Button */}
          <Button onClick={startARView} className="w-full md:w-auto">
            <Camera className="w-4 h-4 mr-2" />
            Start AR-Guided Repair
          </Button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Introduction */}
            {guide.introduction && (
              <Card className="mb-8">
                <CardContent className="p-6">
                  <h2 className="text-xl font-bold text-neutral-900 mb-3">
                    Introduction
                  </h2>
                  <p className="text-neutral-700">
                    {guide.introduction}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Safety Warnings */}
            {guide.warnings && guide.warnings.length > 0 && (
              <Card className="mb-8 border-amber-200 bg-amber-50">
                <CardContent className="p-6">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h3 className="font-semibold text-amber-900 mb-2">
                        Safety Warnings
                      </h3>
                      <ul className="space-y-1 text-amber-800">
                        {guide.warnings.map((warning: string, idx: number) => (
                          <li key={idx}>• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Steps */}
            <div className="space-y-4">
              {guide.steps.map((step: any) => {
                const isExpanded = expandedSteps.has(step.number);
                const isCompleted = completedSteps.has(step.number);

                return (
                  <Card key={step.number} className={isCompleted ? 'opacity-60' : ''}>
                    <CardContent className="p-6">
                      {/* Step Header */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3 flex-1">
                          <button
                            onClick={() => toggleComplete(step.number)}
                            className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                              isCompleted
                                ? 'bg-green-600 border-green-600'
                                : 'border-neutral-300 hover:border-neutral-400'
                            }`}
                          >
                            {isCompleted && (
                              <CheckCircle className="w-4 h-4 text-white" />
                            )}
                          </button>
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-neutral-900">
                              Step {step.number}: {step.title}
                            </h3>
                          </div>
                        </div>
                        <button
                          onClick={() => toggleStep(step.number)}
                          className="text-neutral-600 hover:text-neutral-900"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}
                        </button>
                      </div>

                      {/* Step Content */}
                      {isExpanded && (
                        <div>
                          <p className="text-neutral-700 mb-4">
                            {step.content}
                          </p>

                          {/* Step Image */}
                          <div className="aspect-video bg-gradient-to-br from-neutral-100 to-neutral-200 rounded-lg mb-4 flex items-center justify-center">
                            <Camera className="w-16 h-16 text-neutral-400" />
                            <span className="text-sm text-neutral-500 ml-2">
                              {step.image}
                            </span>
                          </div>

                          {/* Warnings */}
                          {step.warnings && step.warnings.length > 0 && (
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                              <div className="flex items-start gap-2">
                                <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                                <div className="text-sm text-amber-800">
                                  {step.warnings.map((warning: string, idx: number) => (
                                    <div key={idx}>• {warning}</div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Tips */}
                          {step.tips && step.tips.length > 0 && (
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                              <div className="text-sm text-blue-800">
                                <div className="font-semibold mb-1">💡 Tips:</div>
                                {step.tips.map((tip: string, idx: number) => (
                                  <div key={idx}>• {tip}</div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Completion */}
            {completedSteps.size === guide.steps.length && (
              <Card className="mt-8 border-green-200 bg-green-50">
                <CardContent className="p-6 text-center">
                  <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
                  <h3 className="text-xl font-bold text-green-900 mb-2">
                    Repair Complete!
                  </h3>
                  <p className="text-green-800">
                    Great job! Your {guide.brand} {guide.model} battery replacement is complete.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-8 space-y-6">
              {/* Tools */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="font-semibold text-neutral-900 mb-4">
                    Tools Required
                  </h3>
                  <ul className="space-y-2">
                    {guide.tools.map((tool: any, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-neutral-700">
                        <span className={tool.required ? 'text-red-500' : 'text-neutral-400'}>
                          {tool.required ? '•' : '◦'}
                        </span>
                        {tool.name}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Parts */}
              {guide.parts && guide.parts.length > 0 && (
                <Card>
                  <CardContent className="p-6">
                    <h3 className="font-semibold text-neutral-900 mb-4">
                      Parts Needed
                    </h3>
                    <ul className="space-y-3">
                      {guide.parts.map((part: any, idx: number) => (
                        <li key={idx}>
                          <a 
                            href={part.link}
                            className="text-sm text-blue-600 hover:text-blue-700"
                          >
                            {part.name} →
                          </a>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Progress */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="font-semibold text-neutral-900 mb-4">
                    Progress
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-neutral-600">
                      <span>Completed</span>
                      <span>{completedSteps.size} / {guide.steps.length}</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full transition-all"
                        style={{ width: `${(completedSteps.size / guide.steps.length) * 100}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Sources */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="font-semibold text-neutral-900 mb-4">
                    Sources
                  </h3>
                  <div className="space-y-2 text-sm text-neutral-600">
                    {guide.sources.map((source: string, idx: number) => (
                      <div key={idx} className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        {source}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
