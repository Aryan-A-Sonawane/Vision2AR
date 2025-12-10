import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Button } from './ui/Button';
import { Camera, X, ChevronLeft, ChevronRight, RotateCcw, Volume2, VolumeX } from 'lucide-react';

interface ARViewProps {
  currentStep: number;
  totalSteps: number;
  stepTitle: string;
  stepDescription: string;
  stepImage?: string;
  tutorialId?: number;
  category?: string;
  onStepChange: (step: number) => void;
  onClose: () => void;
}

export default function ARView({
  currentStep,
  totalSteps,
  stepTitle,
  stepDescription,
  stepImage,
  tutorialId = 1,
  category = 'laptop',
  onStepChange,
  onClose
}: ARViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const detectionIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const speechSynthRef = useRef<SpeechSynthesisUtterance | null>(null);
  
  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [overlayVisible, setOverlayVisible] = useState(true);
  const [detectionActive, setDetectionActive] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [arOverlays, setArOverlays] = useState<any[]>([]);
  const [guidanceText, setGuidanceText] = useState<string>('');
  const [anchorsLoaded, setAnchorsLoaded] = useState(false);

  // Initialize camera on mount
  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
      stopDetection();
      stopSpeech();
    };
  }, []);

  // Process reference image when step changes
  useEffect(() => {
    if (cameraReady && stepImage) {
      processReferenceImage();
    }
  }, [currentStep, cameraReady, stepImage]);

  // Auto-speak step description when step changes
  useEffect(() => {
    if (ttsEnabled && stepDescription) {
      speakText(stepDescription);
    }
  }, [currentStep, stepDescription, ttsEnabled]);

  const startCamera = async () => {
    try {
      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play();
          setCameraReady(true);
        };
      }
    } catch (err) {
      console.error('Camera access error:', err);
      setError('Unable to access camera. Please grant camera permissions.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const handlePreviousStep = () => {
    if (currentStep > 0) {
      onStepChange(currentStep - 1);
    }
  };

  const handleNextStep = () => {
    if (currentStep < totalSteps - 1) {
      onStepChange(currentStep + 1);
    }
  };

  // Text-to-Speech Functions
  const speakText = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) {
      console.warn('Text-to-speech not supported');
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9; // Slightly slower for clarity
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    speechSynthRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, []);

  const stopSpeech = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleTTS = () => {
    if (ttsEnabled) {
      stopSpeech();
    }
    setTtsEnabled(!ttsEnabled);
  };

  // AR Detection Functions
  const processReferenceImage = async () => {
    if (!stepImage) return;

    try {
      console.log('[AR] Processing reference image for step', currentStep);
      
      // Fetch the displayed image and convert to base64
      let imageData: string | null = null;
      try {
        const imgResponse = await fetch(stepImage);
        const blob = await imgResponse.blob();
        imageData = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(blob);
        });
      } catch (imgErr) {
        console.warn('[AR] Could not fetch image, sending URL only:', imgErr);
      }
      
      const response = await fetch('http://localhost:8000/api/ar/process-reference', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tutorial_id: tutorialId,
          step_number: currentStep,
          image_url: stepImage,
          image_data: imageData,
          category: category
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('[AR] Reference anchors loaded:', data.anchors_count);
      setAnchorsLoaded(data.success && data.anchors_count > 0);
      
      if (data.success) {
        setGuidanceText(`Found ${data.anchors_count} components to detect`);
      }
    } catch (err) {
      console.error('[AR] Reference processing failed:', err);
      setGuidanceText('Reference image processing unavailable');
    }
  };

  const startDetection = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    // Capture frame from video and send to detection API
    const captureAndDetect = async () => {
      if (!videoRef.current || !canvasRef.current || !detectionActive) return;

      try {
        // Create temporary canvas to capture frame
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = videoRef.current.videoWidth;
        tempCanvas.height = videoRef.current.videoHeight;
        const ctx = tempCanvas.getContext('2d');
        
        if (!ctx) return;

        // Draw current video frame
        ctx.drawImage(videoRef.current, 0, 0);
        const frameData = tempCanvas.toDataURL('image/jpeg', 0.7);

        // Send to detection API
        const response = await fetch('http://localhost:8000/api/ar/detect-live', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tutorial_id: tutorialId,
            step_number: currentStep,
            frame_data: frameData
          })
        });

        if (!response.ok) return;

        const data = await response.json();
        
        if (data.success) {
          setArOverlays(data.matched_components || []);
          setGuidanceText(data.guidance || '');
          
          // Draw overlays on canvas
          drawOverlays(data.matched_components || []);
        }
      } catch (err) {
        console.error('[AR] Detection error:', err);
      }
    };

    // Start detection loop (5 FPS)
    detectionIntervalRef.current = setInterval(captureAndDetect, 200);
  };

  const stopDetection = () => {
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
      detectionIntervalRef.current = null;
    }
    setArOverlays([]);
    clearCanvas();
  };

  const drawOverlays = (components: any[]) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Match canvas size to video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw overlays for each matched component
    components.forEach((comp, index) => {
      // Draw bounding box/circle
      ctx.strokeStyle = comp.action === 'remove' ? '#ef4444' : '#22c55e';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(canvas.width * 0.5, canvas.height * 0.5, 50 + index * 20, 0, Math.PI * 2);
      ctx.stroke();

      // Draw label
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 16px sans-serif';
      ctx.fillText(
        `${comp.label} - ${comp.action}`,
        canvas.width * 0.5 - 50,
        canvas.height * 0.5 - 70 - index * 20
      );
    });
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  const toggleDetection = async () => {
    if (!anchorsLoaded && !detectionActive) {
      setGuidanceText('Loading reference image first...');
      await processReferenceImage();
    }

    if (!detectionActive) {
      console.log('[AR] Starting component detection');
      setDetectionActive(true);
      startDetection();
    } else {
      console.log('[AR] Stopping component detection');
      setDetectionActive(false);
      stopDetection();
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black">
      {/* Camera Feed */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Canvas for AR Overlays */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />

      {/* Error Message */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-80">
          <div className="bg-white rounded-lg p-6 max-w-md text-center">
            <Camera className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Camera Access Required</h3>
            <p className="text-neutral-600 mb-4">{error}</p>
            <Button onClick={onClose} variant="primary">
              Return to Tutorial
            </Button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {!cameraReady && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-80">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p>Initializing camera...</p>
          </div>
        </div>
      )}

      {/* AR Overlay UI */}
      {cameraReady && overlayVisible && (
        <>
          {/* Top Bar - Close and Settings */}
          <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent p-4">
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-white hover:bg-white/20"
              >
                <X className="w-5 h-5 mr-2" />
                Exit AR
              </Button>
              <div className="flex items-center gap-2">
                {/* TTS Toggle */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleTTS}
                  className="text-white hover:bg-white/20"
                  title={ttsEnabled ? 'Mute voice' : 'Enable voice'}
                >
                  {ttsEnabled ? (
                    <Volume2 className={`w-4 h-4 ${isSpeaking ? 'animate-pulse' : ''}`} />
                  ) : (
                    <VolumeX className="w-4 h-4" />
                  )}
                </Button>

                {/* Detection Toggle */}
                <Button
                  variant={detectionActive ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={toggleDetection}
                  className={detectionActive ? '' : 'text-white hover:bg-white/20'}
                >
                  <Camera className="w-4 h-4 mr-2" />
                  {detectionActive ? 'Detecting...' : 'Detect Parts'}
                </Button>
              </div>
            </div>
          </div>

          {/* Center - Step Information Card */}
          <div className="absolute top-20 left-4 right-4 md:left-1/2 md:-translate-x-1/2 md:max-w-2xl">
            <div className="bg-black/70 backdrop-blur-md rounded-lg p-4 text-white border border-white/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold">
                  Step {currentStep + 1} of {totalSteps}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setOverlayVisible(false)}
                  className="text-white hover:bg-white/20 h-6 px-2"
                >
                  Hide
                </Button>
              </div>
              <h3 className="text-lg font-bold mb-2">{stepTitle}</h3>
              <p className="text-sm text-white/90 leading-relaxed">
                {stepDescription}
              </p>
              
              {/* AR Guidance Text */}
              {guidanceText && detectionActive && (
                <div className="mt-3 p-2 bg-primary-600/50 rounded text-sm">
                  {guidanceText}
                </div>
              )}

              {/* Avatar Speaking Indicator */}
              {isSpeaking && ttsEnabled && (
                <div className="mt-3 flex items-center gap-2 text-sm">
                  <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center animate-pulse">
                    <Volume2 className="w-4 h-4" />
                  </div>
                  <span className="text-white/90">Speaking...</span>
                </div>
              )}
              
              {/* Reference Image Thumbnail */}
              {stepImage && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-xs text-white/70">Reference:</span>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={stepImage}
                    alt="Reference"
                    className="h-16 w-auto rounded border border-white/30"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Bottom Bar - Navigation Controls */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
            <div className="max-w-2xl mx-auto">
              {/* Step Progress Bar */}
              <div className="mb-4">
                <div className="h-2 bg-white/20 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 transition-all duration-300"
                    style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
                  />
                </div>
              </div>

              {/* Navigation Buttons */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  size="lg"
                  onClick={handlePreviousStep}
                  disabled={currentStep === 0}
                  className="flex-1 bg-white/10 border-white/30 text-white hover:bg-white/20 disabled:opacity-30"
                >
                  <ChevronLeft className="w-5 h-5 mr-2" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => startCamera()}
                  className="bg-white/10 border-white/30 text-white hover:bg-white/20"
                >
                  <RotateCcw className="w-5 h-5" />
                </Button>
                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleNextStep}
                  disabled={currentStep === totalSteps - 1}
                  className="flex-1"
                >
                  {currentStep === totalSteps - 1 ? 'Complete' : 'Next'}
                  <ChevronRight className="w-5 h-5 ml-2" />
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Show Overlay Button (when hidden) */}
      {cameraReady && !overlayVisible && (
        <button
          onClick={() => setOverlayVisible(true)}
          className="absolute top-4 right-4 bg-primary-600 hover:bg-primary-700 text-white rounded-full p-3 shadow-lg"
        >
          <Camera className="w-6 h-6" />
        </button>
      )}

      {/* AR Detection Indicators */}
      {detectionActive && (
        <div className="absolute top-24 right-4 bg-green-500 text-white text-xs px-3 py-1 rounded-full flex items-center gap-2">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
          Scanning...
        </div>
      )}
    </div>
  );
}
