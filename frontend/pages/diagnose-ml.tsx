import { useState, useRef } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  images?: string[];
  timestamp: string;
}

interface CurrentUnderstanding {
  confidence: number;
  top_cause?: string;
  evidence?: any;
}

export default function MLDiagnosisPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [userInput, setUserInput] = useState('');
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [understanding, setUnderstanding] = useState<CurrentUnderstanding | null>(null);
  const [diagnosis, setDiagnosis] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedImages(prev => [...prev, ...files]);
    }
  };

  const removeImage = (index: number) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  const startDiagnosis = async () => {
    if (!userInput.trim()) {
      alert('Please describe the issue');
      return;
    }

    setIsLoading(true);

    try {
      // Convert images to base64
      const imageData = await Promise.all(
        selectedImages.map(file => fileToBase64(file))
      );

      const response = await fetch('http://localhost:8000/api/v2/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_model: 'lenovo_ideapad_5', // TODO: Let user select
          issue_description: userInput,
          images: imageData.length > 0 ? imageData : null,
          video_url: null
        })
      });

      const data = await response.json();

      // Add user message
      setMessages(prev => [...prev, {
        role: 'user',
        content: userInput,
        images: imageData,
        timestamp: new Date().toISOString()
      }]);

      // Check if diagnosis complete
      if (data.diagnosis) {
        setDiagnosis(data.diagnosis);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Diagnosis Complete!\n\nCause: ${data.diagnosis.cause}\nConfidence: ${(data.diagnosis.confidence * 100).toFixed(0)}%\n\nEasy Fix: ${data.diagnosis.easy_fix}`,
          timestamp: new Date().toISOString()
        }]);
      } else if (data.next_question) {
        // Add assistant question
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.next_question.text,
          timestamp: new Date().toISOString()
        }]);
        setCurrentQuestion(data.next_question);
      }

      setSessionId(data.session_id);
      setUnderstanding(data.current_understanding);
      setUserInput('');
      setSelectedImages([]);

    } catch (error) {
      console.error('Diagnosis error:', error);
      alert('Failed to connect to diagnosis service');
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!userInput.trim()) {
      alert('Please provide an answer');
      return;
    }

    setIsLoading(true);

    try {
      const imageData = await Promise.all(
        selectedImages.map(file => fileToBase64(file))
      );

      const response = await fetch('http://localhost:8000/api/v2/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answer_text: userInput,
          images: imageData.length > 0 ? imageData : null,
          video_url: null
        })
      });

      const data = await response.json();

      // Add user message
      setMessages(prev => [...prev, {
        role: 'user',
        content: userInput,
        images: imageData,
        timestamp: new Date().toISOString()
      }]);

      // Check result
      if (data.diagnosis) {
        setDiagnosis(data.diagnosis);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Diagnosis Complete!\n\nCause: ${data.diagnosis.cause.replace(/_/g, ' ')}\nConfidence: ${(data.diagnosis.confidence * 100).toFixed(0)}%\n\n${data.diagnosis.easy_fix}\n\nSolution Steps:\n${data.diagnosis.solution_steps.map((step: string, i: number) => `${i + 1}. ${step}`).join('\n')}`,
          timestamp: new Date().toISOString()
        }]);
      } else if (data.next_question) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.next_question.text,
          timestamp: new Date().toISOString()
        }]);
        setCurrentQuestion(data.next_question);
      }

      setUnderstanding(data.current_understanding);
      setUserInput('');
      setSelectedImages([]);

    } catch (error) {
      console.error('Answer error:', error);
      alert('Failed to process answer');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">ML-Powered Laptop Diagnosis</h1>
        <p className="text-gray-400 mb-8">Describe your issue with text, photos, or videos</p>

        {/* Current Understanding Panel */}
        {understanding && (
          <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
            <h3 className="font-semibold mb-2">Current Understanding</h3>
            <div className="flex items-center gap-4">
              <div>
                <span className="text-gray-400">Confidence:</span>
                <span className="ml-2 text-green-400 font-bold">
                  {(understanding.confidence * 100).toFixed(0)}%
                </span>
              </div>
              {understanding.top_cause && (
                <div>
                  <span className="text-gray-400">Suspected:</span>
                  <span className="ml-2 text-blue-400">
                    {understanding.top_cause.replace(/_/g, ' ')}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Conversation History */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6 max-h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <p className="text-gray-500 text-center">Start by describing the issue...</p>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`mb-4 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}
              >
                <div
                  className={`inline-block max-w-[80%] p-3 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-600'
                      : 'bg-gray-700'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.images && msg.images.length > 0 && (
                    <div className="mt-2 flex gap-2 flex-wrap">
                      {msg.images.map((img, i) => (
                        <img
                          key={i}
                          src={img}
                          alt={`attachment-${i}`}
                          className="w-20 h-20 object-cover rounded"
                        />
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Current Question Context */}
        {currentQuestion && !diagnosis && (
          <div className="bg-blue-900/30 border border-blue-500 rounded-lg p-4 mb-4">
            <p className="text-sm text-gray-400 mb-1">Question Type:</p>
            <p className="text-blue-300 font-semibold">{currentQuestion.type}</p>
            {currentQuestion.suggested_media && currentQuestion.suggested_media.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-gray-400">Helpful to provide:</p>
                <div className="flex gap-2 mt-1">
                  {currentQuestion.suggested_media.map((media: string, i: number) => (
                    <span key={i} className="text-xs bg-blue-800 px-2 py-1 rounded">
                      {media.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Input Area */}
        {!diagnosis && (
          <div className="bg-gray-800 rounded-lg p-4">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder={
                sessionId
                  ? "Provide detailed answer... (describe what you see, hear, or observe)"
                  : "Describe your laptop issue in detail..."
              }
              className="w-full bg-gray-700 rounded p-3 mb-3 text-white min-h-[100px] resize-none"
              disabled={isLoading}
            />

            {/* Image Attachments */}
            {selectedImages.length > 0 && (
              <div className="flex gap-2 mb-3 flex-wrap">
                {selectedImages.map((file, idx) => (
                  <div key={idx} className="relative">
                    <img
                      src={URL.createObjectURL(file)}
                      alt={file.name}
                      className="w-20 h-20 object-cover rounded"
                    />
                    <button
                      onClick={() => removeImage(idx)}
                      className="absolute -top-2 -right-2 bg-red-600 rounded-full w-6 h-6 flex items-center justify-center"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-3">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                multiple
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-2"
                disabled={isLoading}
              >
                📷 Add Photos
              </button>
              
              <button
                onClick={sessionId ? submitAnswer : startDiagnosis}
                disabled={isLoading || !userInput.trim()}
                className="flex-1 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-semibold"
              >
                {isLoading ? 'Processing...' : sessionId ? 'Submit Answer' : 'Start Diagnosis'}
              </button>
            </div>
          </div>
        )}

        {/* Diagnosis Result */}
        {diagnosis && (
          <div className="bg-green-900/30 border border-green-500 rounded-lg p-6">
            <h2 className="text-2xl font-bold mb-4">Diagnosis Complete ✓</h2>
            <div className="space-y-3">
              <div>
                <span className="text-gray-400">Issue:</span>
                <span className="ml-2 font-semibold text-green-400">
                  {diagnosis.cause.replace(/_/g, ' ')}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Confidence:</span>
                <span className="ml-2 font-semibold">
                  {(diagnosis.confidence * 100).toFixed(0)}%
                </span>
              </div>
              {diagnosis.easy_fix && (
                <div className="bg-yellow-900/30 border border-yellow-600 rounded p-3 mt-4">
                  <p className="text-yellow-300 font-semibold mb-2">Quick Fix to Try:</p>
                  <p>{diagnosis.easy_fix}</p>
                </div>
              )}
              <div className="mt-4">
                <p className="text-gray-400 mb-2">Solution Steps:</p>
                <ol className="list-decimal list-inside space-y-2">
                  {diagnosis.solution_steps.map((step: string, i: number) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>
              {diagnosis.tools_needed && diagnosis.tools_needed.length > 0 && (
                <div className="mt-4">
                  <p className="text-gray-400 mb-2">Tools Needed:</p>
                  <div className="flex gap-2 flex-wrap">
                    {diagnosis.tools_needed.map((tool: string, i: number) => (
                      <span key={i} className="bg-gray-700 px-3 py-1 rounded">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={() => {
                setSessionId(null);
                setMessages([]);
                setDiagnosis(null);
                setUnderstanding(null);
                setCurrentQuestion(null);
              }}
              className="mt-6 w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded font-semibold"
            >
              Start New Diagnosis
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
