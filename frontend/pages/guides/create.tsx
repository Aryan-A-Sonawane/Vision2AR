import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { 
  ArrowLeft, 
  Plus, 
  X,
  Upload,
  Wrench,
  AlertTriangle,
  Save,
  Eye
} from 'lucide-react';

interface RepairStep {
  number: number;
  title: string;
  content: string;
  image: File | null;
  warnings: string[];
  tips: string[];
}

const DIFFICULTY_OPTIONS = ['Easy', 'Medium', 'Hard'];
const BRAND_OPTIONS = ['Lenovo', 'Dell', 'HP', 'Asus', 'Acer', 'MSI', 'Apple', 'Samsung'];
const CATEGORY_OPTIONS = ['Troubleshooting', 'Replacement', 'Upgrade'];

export default function CreateGuide() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    title: '',
    brand: '',
    model: '',
    category: 'Replacement',
    difficulty: 'Medium',
    estimatedTime: '',
    introduction: '',
    tools: [''],
    parts: [''],
    safetyWarnings: ['']
  });

  const [steps, setSteps] = useState<RepairStep[]>([
    {
      number: 1,
      title: '',
      content: '',
      image: null,
      warnings: [],
      tips: []
    }
  ]);

  const [currentStep, setCurrentStep] = useState(0);
  const [previewMode, setPreviewMode] = useState(false);

  const handleFormChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayChange = (field: 'tools' | 'parts' | 'safetyWarnings', index: number, value: string) => {
    const newArray = [...formData[field]];
    newArray[index] = value;
    setFormData(prev => ({ ...prev, [field]: newArray }));
  };

  const addArrayItem = (field: 'tools' | 'parts' | 'safetyWarnings') => {
    setFormData(prev => ({ ...prev, [field]: [...prev[field], ''] }));
  };

  const removeArrayItem = (field: 'tools' | 'parts' | 'safetyWarnings', index: number) => {
    const newArray = formData[field].filter((_: string, i: number) => i !== index);
    setFormData(prev => ({ ...prev, [field]: newArray }));
  };

  const addStep = () => {
    const newStep: RepairStep = {
      number: steps.length + 1,
      title: '',
      content: '',
      image: null,
      warnings: [],
      tips: []
    };
    setSteps([...steps, newStep]);
    setCurrentStep(steps.length);
  };

  const removeStep = (index: number) => {
    if (steps.length > 1) {
      const newSteps = steps.filter((_: RepairStep, i: number) => i !== index);
      // Renumber steps
      newSteps.forEach((step: RepairStep, i: number) => {
        step.number = i + 1;
      });
      setSteps(newSteps);
      if (currentStep >= newSteps.length) {
        setCurrentStep(newSteps.length - 1);
      }
    }
  };

  const updateStep = (index: number, field: keyof RepairStep, value: any) => {
    const newSteps = [...steps];
    (newSteps[index] as any)[field] = value;
    setSteps(newSteps);
  };

  const addStepItem = (stepIndex: number, field: 'warnings' | 'tips', value: string) => {
    if (!value.trim()) return;
    const newSteps = [...steps];
    newSteps[stepIndex][field].push(value);
    setSteps(newSteps);
  };

  const removeStepItem = (stepIndex: number, field: 'warnings' | 'tips', itemIndex: number) => {
    const newSteps = [...steps];
    newSteps[stepIndex][field].splice(itemIndex, 1);
    setSteps(newSteps);
  };

  const handleImageUpload = (stepIndex: number, file: File) => {
    const newSteps = [...steps];
    newSteps[stepIndex].image = file;
    setSteps(newSteps);
  };

  const handleSubmit = async () => {
    // Validate form
    if (!formData.title || !formData.brand || !formData.model) {
      alert('Please fill in all required fields (Title, Brand, Model)');
      return;
    }

    if (steps.some((step: RepairStep) => !step.title || !step.content)) {
      alert('Please complete all step titles and descriptions');
      return;
    }

    // In production, this would submit to API
    console.log('Submitting guide:', { formData, steps });
    
    // Mock success
    alert('Guide submitted successfully! It will be reviewed before publishing.');
    router.push('/guides');
  };

  const currentStepData = steps[currentStep];

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link 
            href="/guides"
            className="inline-flex items-center text-neutral-600 hover:text-neutral-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to guides
          </Link>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-neutral-900">
                Create Repair Guide
              </h1>
              <p className="text-neutral-600 mt-1">
                Share your repair knowledge with the community
              </p>
            </div>
            <div className="flex gap-3">
              <Button 
                variant="outline" 
                onClick={() => setPreviewMode(!previewMode)}
              >
                <Eye className="w-4 h-4 mr-2" />
                {previewMode ? 'Edit' : 'Preview'}
              </Button>
              <Button onClick={handleSubmit}>
                <Save className="w-4 h-4 mr-2" />
                Submit Guide
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">
                    Guide Title *
                  </label>
                  <Input
                    placeholder="e.g., Battery Replacement"
                    value={formData.title}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleFormChange('title', e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Brand *
                    </label>
                    <select
                      value={formData.brand}
                      onChange={(e) => handleFormChange('brand', e.target.value)}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
                    >
                      <option value="">Select brand</option>
                      {BRAND_OPTIONS.map(brand => (
                        <option key={brand} value={brand.toLowerCase()}>
                          {brand}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Model *
                    </label>
                    <Input
                      placeholder="e.g., IdeaPad 5"
                      value={formData.model}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleFormChange('model', e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Category
                    </label>
                    <select
                      value={formData.category}
                      onChange={(e) => handleFormChange('category', e.target.value)}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
                    >
                      {CATEGORY_OPTIONS.map(cat => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Difficulty
                    </label>
                    <select
                      value={formData.difficulty}
                      onChange={(e) => handleFormChange('difficulty', e.target.value)}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
                    >
                      {DIFFICULTY_OPTIONS.map(diff => (
                        <option key={diff} value={diff}>
                          {diff}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      Time Estimate
                    </label>
                    <Input
                      placeholder="e.g., 30-45 min"
                      value={formData.estimatedTime}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleFormChange('estimatedTime', e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">
                    Introduction
                  </label>
                  <Textarea
                    placeholder="Describe what this guide will accomplish and when it's needed..."
                    value={formData.introduction}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleFormChange('introduction', e.target.value)}
                    rows={4}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Tools, Parts, Warnings */}
            <Card>
              <CardHeader>
                <CardTitle>Requirements & Safety</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Tools */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">
                    Tools Required
                  </label>
                  {formData.tools.map((tool: string, index: number) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <Input
                        placeholder="e.g., Phillips #0 Screwdriver"
                        value={tool}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleArrayChange('tools', index, e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeArrayItem('tools', index)}
                        disabled={formData.tools.length === 1}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addArrayItem('tools')}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Tool
                  </Button>
                </div>

                {/* Parts */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">
                    Parts Needed
                  </label>
                  {formData.parts.map((part: string, index: number) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <Input
                        placeholder="e.g., Replacement Battery"
                        value={part}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleArrayChange('parts', index, e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeArrayItem('parts', index)}
                        disabled={formData.parts.length === 1}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addArrayItem('parts')}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Part
                  </Button>
                </div>

                {/* Safety Warnings */}
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">
                    Safety Warnings
                  </label>
                  {formData.safetyWarnings.map((warning: string, index: number) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <Input
                        placeholder="e.g., Disconnect power before starting"
                        value={warning}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleArrayChange('safetyWarnings', index, e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeArrayItem('safetyWarnings', index)}
                        disabled={formData.safetyWarnings.length === 1}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addArrayItem('safetyWarnings')}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Warning
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Repair Steps */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Repair Steps ({steps.length})</CardTitle>
                  <Button onClick={addStep} size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Step
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {/* Step Navigator */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                  {steps.map((step: RepairStep, index: number) => (
                    <button
                      key={index}
                      onClick={() => setCurrentStep(index)}
                      className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors ${
                        currentStep === index
                          ? 'bg-neutral-900 text-white'
                          : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                      }`}
                    >
                      Step {step.number}
                    </button>
                  ))}
                </div>

                {/* Current Step Editor */}
                {currentStepData && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Step Title *
                      </label>
                      <Input
                        placeholder="e.g., Remove Bottom Cover"
                        value={currentStepData.title}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStep(currentStep, 'title', e.target.value)}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Instructions *
                      </label>
                      <Textarea
                        placeholder="Describe what to do in this step..."
                        value={currentStepData.content}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateStep(currentStep, 'content', e.target.value)}
                        rows={6}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Step Image
                      </label>
                      <div className="border-2 border-dashed border-neutral-300 rounded-lg p-8 text-center hover:border-neutral-400 transition-colors">
                        <Upload className="w-12 h-12 text-neutral-400 mx-auto mb-3" />
                        <p className="text-sm text-neutral-600 mb-2">
                          {currentStepData.image ? currentStepData.image.name : 'Click to upload or drag and drop'}
                        </p>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => e.target.files && handleImageUpload(currentStep, e.target.files[0])}
                          className="hidden"
                          id="image-upload"
                        />
                        <label htmlFor="image-upload">
                          <Button variant="outline" size="sm" onClick={() => document.getElementById('image-upload')?.click()}>
                            Choose File
                          </Button>
                        </label>
                      </div>
                    </div>

                    {/* Warnings for this step */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Step Warnings (Optional)
                      </label>
                      <div className="space-y-2">
                        {currentStepData.warnings.map((warning: string, index: number) => (
                          <div key={index} className="flex items-center gap-2 text-sm text-amber-800 bg-amber-50 px-3 py-2 rounded-lg">
                            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                            <span className="flex-1">{warning}</span>
                            <button
                              onClick={() => removeStepItem(currentStep, 'warnings', index)}
                              className="text-amber-600 hover:text-amber-800"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input
                            placeholder="Add a warning..."
                            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                              if (e.key === 'Enter') {
                                const target = e.target as HTMLInputElement;
                                addStepItem(currentStep, 'warnings', target.value);
                                target.value = '';
                              }
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Tips for this step */}
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Step Tips (Optional)
                      </label>
                      <div className="space-y-2">
                        {currentStepData.tips.map((tip: string, index: number) => (
                          <div key={index} className="flex items-center gap-2 text-sm text-blue-800 bg-blue-50 px-3 py-2 rounded-lg">
                            <span className="flex-1">💡 {tip}</span>
                            <button
                              onClick={() => removeStepItem(currentStep, 'tips', index)}
                              className="text-blue-600 hover:text-blue-800"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input
                            placeholder="Add a tip..."
                            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                              if (e.key === 'Enter') {
                                const target = e.target as HTMLInputElement;
                                addStepItem(currentStep, 'tips', target.value);
                                target.value = '';
                              }
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Delete Step */}
                    {steps.length > 1 && (
                      <div className="pt-4 border-t border-neutral-200">
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => removeStep(currentStep)}
                        >
                          <X className="w-4 h-4 mr-2" />
                          Delete This Step
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Guide Preview */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <Card>
                <CardHeader>
                  <CardTitle>Guide Preview</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-neutral-900 mb-2">
                      {formData.title || 'Untitled Guide'}
                    </h3>
                    <p className="text-sm text-neutral-600">
                      {formData.brand && formData.model 
                        ? `${formData.brand.charAt(0).toUpperCase() + formData.brand.slice(1)} ${formData.model}`
                        : 'Brand & Model'}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge>{formData.difficulty}</Badge>
                    <Badge variant="info">{formData.category}</Badge>
                  </div>

                  {formData.estimatedTime && (
                    <div className="text-sm text-neutral-600">
                      ⏱️ {formData.estimatedTime}
                    </div>
                  )}

                  <div className="pt-4 border-t border-neutral-200">
                    <p className="text-xs font-medium text-neutral-500 mb-2">
                      PROGRESS
                    </p>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-neutral-600">Steps</span>
                        <span className="font-medium">{steps.length}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-neutral-600">Tools</span>
                        <span className="font-medium">
                          {formData.tools.filter((t: string) => t.trim()).length}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-neutral-600">Parts</span>
                        <span className="font-medium">
                          {formData.parts.filter((p: string) => p.trim()).length}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-neutral-200">
                    <p className="text-xs text-neutral-500">
                      💡 Your guide will be reviewed by moderators before publishing
                    </p>
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
