import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { ImageUploader } from "@/components/ImageUploader";
import { RegionSelector } from "@/components/RegionSelector";
import { SampleImages } from "@/components/SampleImages";
import { UnifiedResultsPanel } from "@/components/UnifiedResultsPanel";
import { APIService, AIAnalysisResult } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { useScrollAnimation } from "@/hooks/use-scroll-animation";
import { Brain } from "lucide-react";

const Index = () => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [aiResult, setAiResult] = useState<AIAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);
  const [objectSelected, setObjectSelected] = useState(false); // Track if object has been selected

  // Scroll animation hook for main sections
  const mainSection = useScrollAnimation();

  // Auto-enable dark mode on load
  useEffect(() => {
    document.documentElement.classList.add("dark");
    return () => document.documentElement.classList.remove("dark");
  }, []);

  // Check backend connection on component mount
  useEffect(() => {
    const checkBackendConnection = async () => {
      try {
        await APIService.healthCheck();
        setBackendConnected(true);
        toast({
          title: "ANFIS Models Ready",
          description: "AI analysis system is ready for bell pepper assessment",
        });
      } catch (error) {
        console.warn('Backend not available:', error);
        setBackendConnected(false);
        toast({
          title: "ANFIS System Unavailable",
          description: "Please ensure the backend server is running",
          variant: "destructive",
        });
      }
    };

    checkBackendConnection();
  }, []);

  const handleImageSelect = (file: File | null) => {
    setSelectedImage(file);
    if (file) {
      const url = URL.createObjectURL(file);
      setImagePreviewUrl(url);
    } else {
      setImagePreviewUrl(null);
    }
    setAnalysisResult(null);
    setAiResult(null);
    setIsAnalyzing(false);
    setObjectSelected(false); // Reset object selection when new image is selected
  };

  const handleSampleSelect = (imageUrl: string) => {
    setImagePreviewUrl(imageUrl);
    setSelectedImage(null); // No file for sample images
    setAnalysisResult(null);
    setAiResult(null);
    setIsAnalyzing(false);
    setObjectSelected(false); // Reset object selection for sample images
  };

  const handleAnalysisResult = (result: any) => {
    setAnalysisResult(result);
    setObjectSelected(true); // Mark that an object has been selected and analyzed
    setIsAnalyzing(false);
  };

  const handleAnalysisStart = () => {
    setIsAnalyzing(true);
  };

  // ANFIS analysis function
  const handleAIAnalysis = async () => {
    if (!selectedImage || !backendConnected) {
      toast({
        title: "Cannot Analyze",
        description: backendConnected ? "Please select an image" : "ANFIS system not connected",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    try {
      const result = await APIService.analyzeImage(selectedImage, 'ensemble'); // Always use ensemble internally
      setAiResult(result);
      toast({
        title: "ANFIS Analysis Complete",
        description: `Classified as ${result.ai_defect_detection.defect_type} with ${Math.round(result.ai_defect_detection.confidence * 100)}% confidence`,
      });
    } catch (error) {
      console.error('ANFIS analysis failed:', error);
      toast({
        title: "Analysis Failed",
        description: "Failed to analyze image with ANFIS model",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      {/* Hero Section - Landing Page */}
      <section className="min-h-screen flex items-center justify-center px-2 sm:px-4 lg:px-8 py-6 sm:py-8">
        <div className="max-w-7xl mx-auto w-full">
          <div className="flex flex-col-reverse lg:flex-row gap-8 items-center lg:items-stretch min-h-[70vh] w-full">
            {/* Left: Title and Welcome Message */}
            <div className="w-full lg:w-[60%] flex flex-col justify-center animate-fade-in space-y-6 sm:space-y-8 items-center lg:items-start">
              <div className="text-center lg:text-left space-y-4 sm:space-y-6 animate-fade-in w-full">
                <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold text-emphasis leading-tight">
                  ANFIS-Powered Bell Pepper
                  <span className="bg-gradient-to-r from-primary via-accent to-success bg-clip-text text-transparent"> Quality Grading</span>
                </h1>
                <p className="text-base sm:text-xl text-subtle max-w-2xl leading-relaxed mx-auto lg:mx-0">
                  Revolutionize your agricultural quality control with our advanced ANFIS model. 
                  Upload or capture bell pepper images for instant, precise quality assessment.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-2 sm:pt-4 justify-center lg:justify-start">
                  <button className="btn-primary ripple text-base sm:text-lg px-6 sm:px-8 py-3 sm:py-4 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300">
                    Get Started
                  </button>
                  <button className="btn-outline ripple text-base sm:text-lg px-6 sm:px-8 py-3 sm:py-4">
                    Learn More
                  </button>
                </div>
              </div>
            </div>
            {/* Right: Camera View and Upload */}
            <div className="w-full lg:w-[40%] flex flex-col justify-center animate-fade-in items-center">
              <div className="p-4 sm:p-6 space-y-4 w-full max-w-md">
                <h3 className="text-base sm:text-lg font-semibold text-emphasis text-center mb-4">
                  Capture or Upload Image
                </h3>
                <ImageUploader onImageSelect={handleImageSelect} selectedImage={selectedImage} />
              </div>
            </div>
          </div>
        </div>
      </section>
      {/* Main Content - Revealed on Scroll */}
      <section className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-10 sm:py-16 space-y-10 sm:space-y-16">
        {/* Analysis Feature Section */}
        <div 
          ref={mainSection.elementRef}
          className={`animate-fade-in-up ${mainSection.isVisible ? 'animate-in' : ''}`}
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-emphasis mb-4">
              ANFIS-Powered Analysis Features
            </h2>
            <p className="text-lg text-subtle max-w-3xl mx-auto">
              Advanced ANFIS model provides comprehensive bell pepper classification with high accuracy
            </p>
          </div>

          {/* AI Model Selection */}
          {/* Removed AIModelSelector */}

          {/* Analysis Grid */}
          <div className="grid lg:grid-cols-2 gap-8 items-start">
            {/* Left Column: Analysis Controls */}
            <div className="space-y-6">

              {/* AI Analysis Button - Only show after object selection */}
              {selectedImage && backendConnected && objectSelected && (
                <div className="animate-fade-in">
                  <button
                    onClick={handleAIAnalysis}
                    disabled={isAnalyzing}
                    className="w-full btn-primary ripple text-lg px-8 py-4 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? (
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Analyzing with ANFIS...
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-2">
                        <Brain className="w-5 h-5" />
                        Analyze with ANFIS
                      </div>
                    )}
                  </button>
                </div>
              )}

              {/* Object Selection Required Message */}
              {selectedImage && backendConnected && !objectSelected && (
                <div className="animate-fade-in">
                  <div className="text-center p-4 bg-yellow-950/20 rounded-lg border border-yellow-500/20">
                    <p className="text-yellow-300 text-sm">
                      ⚠️ Please select an object in the image below before analyzing with ANFIS
                    </p>
                  </div>
                </div>
              )}

              {/* Object Selection (Legacy) */}
              {imagePreviewUrl && (
                <div className="animate-fade-in">
                  <RegionSelector 
                    imageUrl={imagePreviewUrl} 
                    imageFile={selectedImage} 
                    onAnalysisResult={handleAnalysisResult}
                    onAnalysisStart={handleAnalysisStart}
                  />
                </div>
              )}
            </div>

            {/* Right Column: Results */}
            <div className="space-y-6">
              <div className="animate-fade-in">
                <UnifiedResultsPanel 
                  aiResult={aiResult} 
                  legacyResult={analysisResult} 
                  isAnalyzing={isAnalyzing}
                  showLegacy={!!analysisResult}
                />
              </div>
            </div>
          </div>
        </div>
        {/* History Section */}
        <div className="animate-fade-in">
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-emphasis mb-4">
              Analysis History
            </h2>
            <p className="text-lg text-subtle max-w-3xl mx-auto">
              Track your previous assessments and quality trends over time
            </p>
          </div>
          <div className="bg-card/80 rounded-xl p-8 shadow-lg">
            <div className="text-center text-subtle">
              <p className="text-lg">History feature coming soon...</p>
              <p className="text-sm mt-2">Previous analyses will be stored here for reference</p>
            </div>
          </div>
        </div>
        {/* Recent Results */}
        <div className="animate-fade-in">
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-emphasis mb-4">
              Recent Results
            </h2>
            <p className="text-lg text-subtle max-w-3xl mx-auto">
              View your latest quality assessments and insights
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Placeholder for recent results */}
            <div className="bg-card/80 rounded-xl p-6 text-center shadow-lg">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/20 flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L13.09 8.26L19 7L14.74 12L19 17L13.09 15.74L12 22L10.91 15.74L5 17L9.26 12L5 7L10.91 8.26L12 2Z" fill="currentColor"/>
                </svg>
              </div>
              <h3 className="font-semibold text-emphasis mb-2">Grade A</h3>
              <p className="text-sm text-subtle">Excellent quality, 94% confidence</p>
            </div>
            <div className="bg-card/80 rounded-xl p-6 text-center shadow-lg">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-accent/20 flex items-center justify-center">
                <svg className="w-8 h-8 text-accent" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L13.09 8.26L19 7L14.74 12L19 17L13.09 15.74L12 22L10.91 15.74L5 17L9.26 12L5 7L10.91 8.26L12 2Z" fill="currentColor"/>
                </svg>
              </div>
              <h3 className="font-semibold text-emphasis mb-2">Grade B</h3>
              <p className="text-sm text-subtle">Good quality, 87% confidence</p>
            </div>
            <div className="bg-card/80 rounded-xl p-6 text-center shadow-lg">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-success/20 flex items-center justify-center">
                <svg className="w-8 h-8 text-success" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L13.09 8.26L19 7L14.74 12L19 17L13.09 15.74L12 22L10.91 15.74L5 17L9.26 12L5 7L10.91 8.26L12 2Z" fill="currentColor"/>
                </svg>
              </div>
              <h3 className="font-semibold text-emphasis mb-2">Grade A+</h3>
              <p className="text-sm text-subtle">Premium quality, 98% confidence</p>
            </div>
          </div>
        </div>

        {/* ANFIS Model Section - COMMENTED OUT DUE TO DEFECT DETECTION DISABLED */}
        {/* <div 
          ref={sampleDemosSection.elementRef}
          className={`animate-fade-in-up ${sampleDemosSection.isVisible ? 'animate-in' : ''}`}
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-emphasis mb-4">
              ANFIS Defect Detection
            </h2>
            <p className="text-lg text-subtle max-w-3xl mx-auto">
              Advanced Adaptive Neuro-Fuzzy Inference System for precise defect detection and quality assessment
            </p>
          </div>
          <div className="bg-card/80 rounded-xl p-8 shadow-lg animate-fade-in">
            <ANFISPanel />
          </div>
        </div> */}

        {/* Sample Demos */}
        <div className="animate-fade-in">
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-emphasis mb-4">
              Sample Demonstrations
            </h2>
            <p className="text-lg text-subtle max-w-3xl mx-auto">
              Try our system with pre-loaded sample images to see the analysis in action
            </p>
          </div>
          <div className="bg-card/80 rounded-xl p-8 shadow-lg animate-fade-in">
            <SampleImages onSampleSelect={handleSampleSelect} />
          </div>
        </div>
      </section>
    </div>
  );
};

export default Index;
