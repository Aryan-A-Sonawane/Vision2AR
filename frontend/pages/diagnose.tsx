import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import DebugTerminal, { useDebugTerminal } from '@/components/DebugTerminal';
import { Terminal, ChevronRight, Activity, Wrench, AlertTriangle } from 'lucide-react';

interface Question {
  id: string;
  text: string;
  expected_signal: string;
  cost_level: string;
  response_type?: string;  // "binary" or "text"
}

interface Tutorial {
  id: number;
  title: string;
  brand: string;
  model: string;
  difficulty: string;
  step_count: number;
  category?: string;
}

interface BeliefVector {
  [cause: string]: number;
}

export default function DiagnosePage() {
  const router = useRouter();
  const { device } = router.query;
  const { logs, isOpen, addLog, clearLogs, toggleTerminal } = useDebugTerminal();
  
  const [step, setStep] = useState<'symptoms' | 'questions' | 'result'>('symptoms');
  const [symptoms, setSymptoms] = useState('');
  const [category, setCategory] = useState<string>('PC');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [diagnosisState, setDiagnosisState] = useState<string>('');
  const [initialBelief, setInitialBelief] = useState<BeliefVector | null>(null);
  const [currentBelief, setCurrentBelief] = useState<BeliefVector | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [textAnswer, setTextAnswer] = useState('');
  const [tutorials, setTutorials] = useState<Tutorial[]>([]);
  const [loading, setLoading] = useState(false);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        alert('Image size should be less than 10MB');
        return;
      }
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      addLog('Frontend', `Image selected: ${file.name} (${(file.size / 1024).toFixed(1)}KB)`, null, 'info');
    }
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
    addLog('Frontend', 'Image removed', null, 'info');
  };

  const handleSymptomsSubmit = async () => {
    if (!symptoms.trim()) return;
    
    setLoading(true);
    addLog('Frontend', 'Submitting symptoms to enhanced diagnosis engine...', null, 'info');
    addLog('Frontend', `Category selected: ${category}`, null, 'info');
    if (imagePreview) {
      addLog('Frontend', 'Image attached - BLIP-2 will analyze visual symptoms', null, 'info');
    }
    
    try {
      addLog('Frontend', 'Connecting to http://localhost:8000/api/v2/diagnose/start...', null, 'info');
      
      const response = await fetch('http://localhost:8000/api/v2/diagnose/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text_input: `${category}: ${symptoms}`,
          image_base64: imagePreview ? imagePreview.split(',')[1] : null
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      addLog('Backend', `Session created: ${data.session_id}`, null, 'success');
      addLog('Backend', `Diagnosis state: ${data.diagnosis_state}`, null, 'info');
      
      setSessionId(data.session_id);
      setDiagnosisState(data.diagnosis_state);
      setInitialBelief(data.initial_belief);
      setCurrentBelief(data.current_belief || data.initial_belief);
      
      // Log belief vector
      if (data.initial_belief) {
        const topCauses = Object.entries(data.initial_belief)
          .sort((a, b) => (b[1] as number) - (a[1] as number))
          .slice(0, 5);
        addLog('ML_Model', `Top 5 probable causes:`, {
          causes: topCauses.map(([cause, prob]) => `${cause}: ${((prob as number) * 100).toFixed(1)}%`)
        }, 'info');
      }
      
      if (data.diagnosis_state === 'complete' && data.tutorials) {
        // Immediate diagnosis
        addLog('ML_Model', `Found ${data.tutorials.length} matching tutorials`, null, 'success');
        setTutorials(data.tutorials);
        setStep('result');
      } else if (data.next_question) {
        // Need to ask questions
        addLog('ML_Model', `Generated question: ${data.next_question.text}`, null, 'info');
        setCurrentQuestion(data.next_question);
        setStep('questions');
      } else if (data.diagnosis_state === 'uncertain') {
        addLog('ML_Model', 'Unable to determine cause with confidence', null, 'warning');
        if (data.tutorials) {
          setTutorials(data.tutorials);
          setStep('result');
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      addLog('Frontend', `Connection failed: ${errorMessage}`, null, 'error');
      addLog('Frontend', 'Make sure backend is running on http://localhost:8000', null, 'warning');
      console.error('Diagnosis error:', error);
      alert('Cannot connect to backend server. Please check if the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (answer: 'yes' | 'no' | string) => {
    if (!currentQuestion) return;
    
    // For text questions, require non-empty text answer
    if (currentQuestion.response_type === 'text' && typeof answer === 'string' && answer.trim().length < 3) {
      alert('Please provide a more detailed answer (at least 3 characters)');
      return;
    }
    
    setLoading(true);
    addLog('Frontend', `User answered: ${typeof answer === 'string' && answer.length > 50 ? answer.substring(0, 50) + '...' : answer}`, null, 'info');
    
    try {
      const response = await fetch('http://localhost:8000/api/v2/diagnose/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: currentQuestion.id,
          answer: answer,
          response_type: currentQuestion.response_type || 'binary'
        }),
      });
      
      const data = await response.json();
      addLog('Backend', `Diagnosis state: ${data.diagnosis_state}`, null, 'info');
      
      // Update belief vector
      if (data.current_belief) {
        setCurrentBelief(data.current_belief);
        const topCauses = Object.entries(data.current_belief)
          .sort((a, b) => (b[1] as number) - (a[1] as number))
          .slice(0, 5);
        addLog('ML_Model', 'Belief vector updated:', {
          causes: topCauses.map(([cause, prob]) => `${cause}: ${((prob as number) * 100).toFixed(1)}%`)
        }, 'info');
      }
      
      if (data.diagnosis_state === 'complete' && data.tutorials) {
        // Final diagnosis reached
        addLog('ML_Model', `Diagnosis complete! Found ${data.tutorials.length} tutorials`, null, 'success');
        setTutorials(data.tutorials);
        setTextAnswer(''); // Clear text input
        setStep('result');
      } else if (data.next_question) {
        // Continue with next question
        addLog('ML_Model', `Next question: ${data.next_question.text}`, null, 'info');
        setCurrentQuestion(data.next_question);
        setTextAnswer(''); // Clear text input for next question
      } else if (data.diagnosis_state === 'uncertain') {
        // Uncertain diagnosis
        addLog('ML_Model', 'Unable to determine cause with high confidence', null, 'warning');
        if (data.tutorials) {
          setTutorials(data.tutorials);
          setTextAnswer('');
          setStep('result');
        }
      }
    } catch (error) {
      addLog('Frontend', `Error: ${error}`, null, 'error');
      console.error('Answer processing error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
      {/* Header */}
      <header className="border-b border-neutral-200 bg-white shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => router.back()}>
              ← Back
            </Button>
            <div className="text-center">
              <h1 className="text-xl font-semibold text-neutral-900">AI Laptop Diagnosis</h1>
              <p className="text-xs text-neutral-500 mt-1">Powered by 6,331+ repair guides</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={toggleTerminal}>
                <Terminal className="w-4 h-4" />
              </Button>
              <Button variant="outline" onClick={() => router.push('/guides')}>
                Browse Guides
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Symptoms Input */}
        {step === 'symptoms' && (
          <div className="animate-fade-in space-y-6">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Activity className="w-6 h-6 text-primary-600" />
                  Describe Your Problem
                </CardTitle>
                <CardDescription className="text-base">
                  Tell us what&apos;s happening with your device. Be as detailed as possible for accurate diagnosis.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Category Selection */}
                <div>
                  <label className="block text-sm font-semibold text-neutral-700 mb-3">
                    Device Category
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {['PC', 'Mac', 'Computer Hardware'].map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setCategory(cat)}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          category === cat
                            ? 'border-primary-600 bg-primary-50 text-primary-900'
                            : 'border-neutral-200 bg-white text-neutral-700 hover:border-neutral-300'
                        }`}
                      >
                        <div className="text-center">
                          <div className="text-lg font-semibold">{cat}</div>
                          <div className="text-xs text-neutral-500 mt-1">
                            {cat === 'PC' && '3,592 guides'}
                            {cat === 'Mac' && '2,224 guides'}
                            {cat === 'Computer Hardware' && '515 guides'}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Symptom Description with Modern Image Upload */}
                <div>
                  <label className="block text-sm font-semibold text-neutral-700 mb-2">
                    What&apos;s wrong?
                  </label>
                  <div className="flex gap-3">
                    {/* Main textarea with inline image button */}
                    <div className="flex-1 relative">
                      <Textarea
                        placeholder="Example: My laptop won't turn on. The power LED doesn't light up, and there's no fan noise when I press the power button..."
                        rows={6}
                        value={symptoms}
                        onChange={(e) => setSymptoms(e.target.value)}
                        className="text-base pr-14"
                      />
                      {/* Modern image button in bottom-right corner */}
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageSelect}
                        className="hidden"
                        id="image-upload"
                      />
                      <label
                        htmlFor="image-upload"
                        className="absolute bottom-3 right-3 cursor-pointer bg-neutral-100 hover:bg-neutral-200 rounded-lg p-2 transition-all shadow-sm border border-neutral-300"
                        title="Add image"
                      >
                        <span className="text-xl">📷</span>
                      </label>
                    </div>
                    
                    {/* Vertical image thumbnails bar */}
                    {imagePreview && (
                      <div className="w-24 space-y-2">
                        <div className="relative group border-2 border-primary-400 rounded-lg p-1 bg-white">
                          <img
                            src={imagePreview}
                            alt="Preview"
                            className="w-full h-20 object-cover rounded"
                          />
                          <button
                            onClick={removeImage}
                            className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center hover:bg-red-600 transition-colors text-xs opacity-0 group-hover:opacity-100"
                          >
                            ✕
                          </button>
                          <div className="text-[10px] text-center text-neutral-600 mt-1">
                            BLIP-2
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  {imagePreview && (
                    <p className="text-xs text-neutral-600 mt-2 flex items-center gap-1">
                      <span>✓</span>
                      <span>Image ready for AI visual analysis</span>
                    </p>
                  )}
                </div>

                <Button
                  size="lg"
                  onClick={handleSymptomsSubmit}
                  disabled={!symptoms.trim() || loading}
                  className="w-full"
                >
                  {loading ? 'Analyzing...' : 'Start Diagnosis'}
                  <ChevronRight className="w-5 h-5 ml-2" />
                </Button>
              </CardContent>
            </Card>

            {/* Quick Symptoms */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Common Issues</CardTitle>
                <CardDescription>Click to use as starting point</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {[
                    "Won't turn on",
                    'Screen flickering',
                    'Keyboard not working',
                    'Overheating and shutting down',
                    'No sound output',
                    'Battery not charging',
                    'Blue screen errors',
                    'WiFi not connecting'
                  ].map((issue) => (
                    <Badge
                      key={issue}
                      variant="default"
                      className="cursor-pointer hover:bg-primary-600 hover:text-white transition-colors px-3 py-1"
                      onClick={() => setSymptoms(issue)}
                    >
                      {issue}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Dynamic Questions */}
        {step === 'questions' && currentQuestion && (
          <div className="animate-fade-in space-y-6">
            {/* Belief Vector Visualization */}
            {currentBelief && (
              <Card className="shadow-lg border-primary-200">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Activity className="w-5 h-5 text-primary-600" />
                      Current Diagnosis Confidence
                    </span>
                    <Badge variant="info">
                      {Math.round(Math.max(...Object.values(currentBelief)) * 100)}%
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(currentBelief)
                      .sort((a, b) => (b[1] as number) - (a[1] as number))
                      .slice(0, 5)
                      .map(([cause, prob], idx) => (
                        <div key={cause}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-neutral-700">
                              {idx === 0 && '🎯 '}
                              {cause.replace(/_/g, ' ')}
                            </span>
                            <span className="text-sm text-neutral-600">
                              {((prob as number) * 100).toFixed(1)}%
                            </span>
                          </div>
                          <Progress
                            value={(prob as number) * 100}
                            size="sm"
                          />
                        </div>
                      ))}
                  </div>
                  <p className="text-xs text-neutral-500 mt-4">
                    We&apos;ll stop asking questions when confidence reaches 60% or higher
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Question Card */}
            <Card className="border-2 border-primary-600 shadow-xl">
              <CardHeader>
                <Badge variant="info" className="w-fit mb-3">
                  {currentQuestion.response_type === 'text' ? '💬 Open Question' : 'Diagnostic Question'}
                </Badge>
                <CardTitle className="text-2xl leading-relaxed">{currentQuestion.text}</CardTitle>
                <CardDescription className="text-base">
                  {currentQuestion.response_type === 'text' 
                    ? 'Describe in your own words - the more detail, the better'
                    : 'Answer based on what you observe with your device'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {currentQuestion.response_type === 'text' ? (
                  // Text input for open-ended questions
                  <div className="space-y-4">
                    <Textarea
                      placeholder="Type your answer here... (e.g., 'Yes, I installed a new graphics driver yesterday' or 'The screen flickers only when the laptop gets warm')"
                      rows={5}
                      value={textAnswer}
                      onChange={(e) => setTextAnswer(e.target.value)}
                      className="text-base"
                    />
                    <Button
                      size="lg"
                      onClick={() => handleAnswer(textAnswer)}
                      disabled={loading || textAnswer.trim().length < 3}
                      className="w-full"
                    >
                      {loading ? '⏳ Processing...' : 'Submit Answer'}
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                  </div>
                ) : (
                  // Binary Yes/No buttons
                  <div className="grid grid-cols-2 gap-4">
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={() => handleAnswer('yes')}
                      disabled={loading}
                      className="h-28 text-xl font-semibold hover:bg-success-50 hover:border-success-600 hover:text-success-700"
                    >
                      {loading ? '⏳ Processing...' : (
                        <div className="flex flex-col items-center gap-2">
                          <span className="text-3xl">✓</span>
                          <span>Yes</span>
                        </div>
                      )}
                    </Button>
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={() => handleAnswer('no')}
                      disabled={loading}
                      className="h-28 text-xl font-semibold hover:bg-danger-50 hover:border-danger-600 hover:text-danger-700"
                    >
                      {loading ? '⏳ Processing...' : (
                        <div className="flex flex-col items-center gap-2">
                          <span className="text-3xl">✗</span>
                          <span>No</span>
                        </div>
                      )}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Question Info */}
            <div className="text-center text-sm text-neutral-600">
              <p>💡 Tip: Answer honestly for the most accurate diagnosis</p>
            </div>
          </div>
        )}

        {/* Diagnosis Result */}
        {step === 'result' && (
          <div className="animate-fade-in space-y-6">
            {/* Success Banner */}
            <Card className="border-2 border-success-500 bg-gradient-to-r from-success-50 to-success-100 shadow-xl">
              <CardHeader>
                <div className="text-center">
                  <div className="text-6xl mb-4">✓</div>
                  <CardTitle className="text-3xl text-success-900">Diagnosis Complete!</CardTitle>
                  <CardDescription className="text-lg text-success-700 mt-2">
                    {diagnosisState === 'complete' 
                      ? `Found ${tutorials.length} matching repair guide${tutorials.length !== 1 ? 's' : ''}`
                      : 'Here are the most relevant tutorials based on your symptoms'
                    }
                  </CardDescription>
                </div>
              </CardHeader>
            </Card>

            {/* Top Probable Cause */}
            {currentBelief && Object.entries(currentBelief).length > 0 && (
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-2">
                    <AlertTriangle className="w-6 h-6 text-warning-600" />
                    Most Likely Cause
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-semibold text-neutral-900">
                        {Object.entries(currentBelief)
                          .sort((a, b) => (b[1] as number) - (a[1] as number))[0][0]
                          .replace(/_/g, ' ')}
                      </p>
                      <p className="text-sm text-neutral-600 mt-1">
                        Based on your symptoms and device behavior
                      </p>
                    </div>
                    <Badge variant="success" className="text-lg px-4 py-2">
                      {Math.round(Math.max(...Object.values(currentBelief)) * 100)}% confidence
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Repair Tutorials */}
            <div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-4 flex items-center gap-2">
                <Wrench className="w-6 h-6 text-primary-600" />
                Recommended Repair Tutorials
              </h3>
              <div className="space-y-4">
                {tutorials.length > 0 ? (
                  tutorials.map((tutorial, idx) => (
                    <Card
                      key={tutorial.id}
                      className="hover:shadow-lg transition-shadow cursor-pointer"
                      onClick={() => router.push(`/tutorial/${tutorial.id}`)}
                    >
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <Badge variant={idx === 0 ? 'success' : 'default'}>
                                {idx === 0 ? '⭐ Best Match' : `#${idx + 1}`}
                              </Badge>
                              <Badge variant="default" className="capitalize">
                                {tutorial.category || category}
                              </Badge>
                              <Badge 
                                variant={
                                  tutorial.difficulty === 'easy' ? 'success' :
                                  tutorial.difficulty === 'hard' ? 'danger' : 'warning'
                                }
                              >
                                {tutorial.difficulty}
                              </Badge>
                            </div>
                            <h4 className="text-lg font-semibold text-neutral-900 mb-2">
                              {tutorial.title}
                            </h4>
                            <div className="flex items-center gap-4 text-sm text-neutral-600">
                              <span>📱 {tutorial.brand}</span>
                              <span>💻 {tutorial.model}</span>
                              <span>📋 {tutorial.step_count} steps</span>
                            </div>
                          </div>
                          <ChevronRight className="w-6 h-6 text-neutral-400" />
                        </div>
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <Card>
                    <CardContent className="p-8 text-center">
                      <p className="text-neutral-600">
                        No specific tutorials found. Try browsing our complete guide library.
                      </p>
                      <Button
                        variant="outline"
                        className="mt-4"
                        onClick={() => router.push('/guides')}
                      >
                        Browse All Guides
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <Button
                size="lg"
                onClick={() => {
                  setStep('symptoms');
                  setSymptoms('');
                  setCurrentQuestion(null);
                  setTutorials([]);
                  setCurrentBelief(null);
                  setInitialBelief(null);
                  clearLogs();
                }}
                className="flex-1"
              >
                🔄 Start New Diagnosis
              </Button>
              <Button
                variant="outline"
                size="lg"
                onClick={() => router.push('/guides')}
              >
                📚 Browse All Guides
              </Button>
            </div>
          </div>
        )}
      </main>
      
      {/* Debug Terminal */}
      <DebugTerminal isOpen={isOpen} onClose={toggleTerminal} logs={logs} />
    </div>
  );
}
