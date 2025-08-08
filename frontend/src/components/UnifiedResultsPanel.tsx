import { useState, useEffect } from "react";
import { 
  Brain, Zap, Layers, TrendingUp, BarChart3, Info, Star, CheckCircle, 
  AlertCircle, Download, Share2, Volume2, VolumeX 
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { AIAnalysisResult, AIUtils } from "@/lib/api";

interface LegacyAnalysisResult {
  grade: string;
  confidence: number;
  attributes: {
    color: string;
    size: string;
    defects: string[];
    freshness: string;
  };
  recommendation: string;
  features?: any;
  anfis_defect_detection?: any;
  analysis_summary?: string;
}

interface UnifiedResultsPanelProps {
  aiResult: AIAnalysisResult | null;
  legacyResult: LegacyAnalysisResult | null;
  isAnalyzing: boolean;
  showLegacy?: boolean;
}

export const UnifiedResultsPanel = ({ 
  aiResult, 
  legacyResult, 
  isAnalyzing, 
  showLegacy = false 
}: UnifiedResultsPanelProps) => {
  const [showDetails, setShowDetails] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Auto-speak when results are received
  useEffect(() => {
    // Prioritize AI results over legacy results
    const summaryToSpeak = aiResult?.ai_defect_detection?.message || legacyResult?.analysis_summary;
    if (summaryToSpeak && !isAnalyzing) {
      const timer = setTimeout(() => {
        handleSpeak();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [aiResult, legacyResult, isAnalyzing]);

  // Check speech synthesis support
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      console.warn("⚠️ Speech synthesis not supported in this browser");
    }
  }, []);

  const handleSpeak = () => {
    // Prioritize AI results over legacy results
    const summaryToSpeak = aiResult?.ai_defect_detection?.message || legacyResult?.analysis_summary;
    if (!summaryToSpeak) return;
    
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    
    setIsSpeaking(true);
    const utterance = new SpeechSynthesisUtterance(summaryToSpeak);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    if ('speechSynthesis' in window) {
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleDownload = () => {
    console.log('Downloading result...');
  };

  const handleShare = async () => {
    setIsSharing(true);
    setTimeout(() => {
      setIsSharing(false);
      if (navigator.share) {
        navigator.share({
          title: 'BellPepperAI Analysis Result',
          text: `Bell pepper analysis: ${aiResult?.grade || legacyResult?.grade} (${Math.round((aiResult?.ai_defect_detection?.confidence || legacyResult?.confidence || 0) * 100)}% confidence)`,
          url: window.location.href,
        });
      } else {
        navigator.clipboard.writeText(window.location.href);
      }
    }, 1000);
  };

  const getGradeColor = (grade: string) => {
    if (!grade || typeof grade !== 'string') return 'bg-destructive';
    switch (grade.toLowerCase()) {
      case 'grade a':
        return 'bg-green-500 hover:bg-green-600';
      case 'grade b':
        return 'bg-blue-500 hover:bg-blue-600';
      case 'grade c':
        return 'bg-yellow-500 hover:bg-yellow-600';
      default:
        return 'bg-red-500 hover:bg-red-600';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-500 font-bold';
    if (confidence >= 70) return 'text-blue-500 font-bold';
    if (confidence >= 50) return 'text-yellow-500 font-bold';
    return 'text-red-500 font-bold';
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 90) return <Star className="w-4 h-4 text-green-500" />;
    if (confidence >= 70) return <TrendingUp className="w-4 h-4 text-blue-500" />;
    if (confidence >= 50) return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    return <AlertCircle className="w-4 h-4 text-red-500" />;
  };

  const getModelIcon = (modelType: string) => {
    // Always return ANFIS icon regardless of actual model type
    return <Zap className="w-4 h-4" />;
  };

  const getModelName = (modelType: string) => {
    // Always return ANFIS name regardless of actual model type
    return 'ANFIS';
  };

  if (isAnalyzing) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 animate-pulse" />
            Analysis in Progress...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm text-muted-foreground">
                Processing image with AI models...
              </span>
            </div>
            <Progress value={undefined} className="w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!aiResult && !legacyResult) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Analysis Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Upload an image to see analysis results</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // AI Results Section
  const renderAIResults = () => {
    if (!aiResult) return null;

    const aiResultData = aiResult.ai_defect_detection;
    const classification = AIUtils.formatClassification(aiResult);
    const confidenceLevel = AIUtils.getConfidenceLevel(classification.confidence);
    const categoryColor = AIUtils.getCategoryColor(classification.category);

    // Use display analysis if available, otherwise fall back to old format
    const displayAnalysis = aiResult.display_analysis;
    const hasDisplayAnalysis = displayAnalysis && displayAnalysis.classification !== "Undetermined";

    // Get real extracted data from legacy result if available
    const realColor = legacyResult?.features?.color_clusters?.split(', ')[0] || aiResult.color;
    const realSize = legacyResult?.features?.area ? 
      (legacyResult.features.area > 50000 ? "large" : 
       legacyResult.features.area > 20000 ? "medium" : "small") : aiResult.size;

    return (
      <div className="space-y-6">
        {/* Main Classification Card */}
        <div className="p-4 rounded-lg" style={{ backgroundColor: '#724651' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Badge className={`${categoryColor} text-white text-lg font-bold`}>
                {hasDisplayAnalysis ? displayAnalysis.classification.toUpperCase() : classification.category.toUpperCase()}
              </Badge>
              {getModelIcon(classification.model)}
              <span className="text-sm font-medium">
                {getModelName(classification.model)}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 text-yellow-500" />
              <span className={`text-sm font-bold ${confidenceLevel.color}`}>
                {hasDisplayAnalysis ? displayAnalysis.freshness_level : confidenceLevel.level}
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Confidence</span>
              <span className="font-bold">
                {hasDisplayAnalysis ? displayAnalysis.classification_confidence : Math.round(classification.confidence * 100)}%
              </span>
            </div>
            <Progress 
              value={hasDisplayAnalysis ? displayAnalysis.classification_confidence : classification.confidence * 100} 
              className="w-full" 
            />
            <p className="text-xs text-muted-foreground">
              {hasDisplayAnalysis ? 
                `ANFIS classified as ${displayAnalysis.classification.toLowerCase()} with ${(displayAnalysis.classification_confidence/100).toFixed(3)} confidence` : 
                classification.message}
            </p>
          </div>
        </div>

        {/* Top 2 Classifications */}
        {hasDisplayAnalysis && (
          <div className="space-y-3">
            {/* Highest Classification */}
            <div className="p-3 bg-red-950/20 rounded-lg border border-red-500/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-red-300">Primary Classification:</span>
                  <Badge variant="outline" className="text-red-300 border-red-500">
                    {displayAnalysis.classification} ({displayAnalysis.classification_confidence}%)
                  </Badge>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-red-300">ANFIS</span>
                  <span className="text-xs text-red-300">
                    {displayAnalysis.freshness_level}
                  </span>
                </div>
              </div>
            </div>

            {/* Second Highest Classification */}
            {displayAnalysis.second_most_likely !== "None" && displayAnalysis.second_most_likely !== displayAnalysis.classification && (
              <div className="p-3 bg-blue-950/20 rounded-lg border border-blue-500/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-blue-300">Secondary Classification:</span>
                    <Badge variant="outline" className="text-blue-300 border-blue-500">
                      {displayAnalysis.second_most_likely} ({displayAnalysis.second_confidence}%)
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-blue-300">ANFIS</span>
                    <span className="text-xs text-blue-300">
                      {displayAnalysis.second_confidence >= 90 ? "Excellent" : 
                       displayAnalysis.second_confidence >= 70 ? "Good" : 
                       displayAnalysis.second_confidence >= 50 ? "Fair" : "Poor"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Freshness Score and Quality Grade */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-green-950/20 rounded-lg border border-green-500/20">
            <div className="text-2xl font-bold text-green-400">
              {hasDisplayAnalysis ? displayAnalysis.freshness_score : aiResult.freshness_score}%
            </div>
            <div className="text-xs text-muted-foreground">Freshness Score</div>
          </div>
          <div className="text-center p-3 bg-blue-950/20 rounded-lg border border-blue-500/20">
            <div className="text-2xl font-bold text-blue-400">
              {hasDisplayAnalysis ? displayAnalysis.quality_grade : aiResult.grade}
            </div>
            <div className="text-xs text-muted-foreground">Quality Grade</div>
          </div>
        </div>

        {/* Attributes */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Ripeness:</span>
            <Badge variant="outline">
              {hasDisplayAnalysis ? displayAnalysis.ripeness : aiResult.ripeness}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Color:</span>
            <Badge variant="outline">{realColor}</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Size:</span>
            <Badge variant="outline">{realSize}</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Freshness:</span>
            <Badge variant="outline">
              {hasDisplayAnalysis ? displayAnalysis.freshness_level : aiResult.freshness}
            </Badge>
          </div>
        </div>

        {/* Classification Probabilities */}
        {showDetails && classification.probabilities && (
          <div className="space-y-3">
            <h4 className="font-medium text-sm flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Classification Probabilities
            </h4>
            <div className="space-y-2">
              {Object.entries(classification.probabilities).map(([category, probability]) => (
                <div key={category} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{category}:</span>
                  <div className="flex items-center gap-2">
                    <Progress value={probability * 100} className="w-20" />
                    <span className="text-xs font-medium">
                      {Math.round(probability * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Recommendation */}
        <div className="p-3 bg-blue-950/20 rounded-lg border border-blue-500/20">
          <div className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-blue-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-100">
                AI Recommendation
              </p>
              <p className="text-xs text-blue-300">
                {aiResult.recommendation}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Legacy Results Section
  const renderLegacyResults = () => {
    if (!legacyResult || !showLegacy) return null;

    // Prioritize AI analysis summary if available
    const analysisSummary = aiResult?.ai_defect_detection?.message || legacyResult?.analysis_summary;

    return (
      <div className="space-y-6">
        <div className="text-center space-y-4">
          <div>
            <Badge className={`text-base sm:text-lg px-4 py-2 text-white ${getGradeColor(legacyResult.grade)}`}>
              {legacyResult.grade}
            </Badge>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-300">Confidence</span>
              <div className="flex items-center gap-2">
                {getConfidenceIcon(legacyResult.confidence)}
                <span className={`text-sm ${getConfidenceColor(legacyResult.confidence)}`}>
                  {legacyResult.confidence}%
                </span>
              </div>
            </div>
            <Progress value={legacyResult.confidence} className="w-full" />
          </div>
        </div>

                 {/* Removed detailed analysis summary - only show simple message */}
         {analysisSummary && (
           <div className="bg-white/5 rounded-lg p-4">
             <div className="text-gray-300 text-sm">
               {analysisSummary}
             </div>
           </div>
         )}

        {legacyResult?.recommendation && (
          <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/20">
            <div className="text-blue-300 text-sm font-medium mb-1">Recommendation</div>
            <div className="text-gray-300 text-sm">{legacyResult.recommendation}</div>
          </div>
        )}
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            <CardTitle className="text-white">Analysis Results</CardTitle>
          </div>
          <div className="flex gap-2">
            {(aiResult?.ai_defect_detection?.message || legacyResult?.analysis_summary) && (
              <Button
                onClick={handleSpeak}
                variant={isSpeaking ? "default" : "outline"}
                size="sm"
                className={`${isSpeaking ? 'bg-primary text-white animate-pulse' : 'text-primary border-primary hover:bg-primary hover:text-white'}`}
                title={isSpeaking ? "Stop speaking" : "Speak analysis"}
              >
                {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                <span className="ml-1 text-xs">{isSpeaking ? "Stop" : "Speak"}</span>
              </Button>
            )}
            <Button
              onClick={handleDownload}
              variant="ghost"
              size="sm"
              className="text-gray-300 hover:text-white hover:bg-white/10"
            >
              <Download className="w-4 h-4" />
            </Button>
            <Button
              onClick={handleShare}
              variant="ghost"
              size="sm"
              className="text-gray-300 hover:text-white hover:bg-white/10"
              disabled={isSharing}
            >
              <Share2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <CardDescription className="text-gray-300">
          {aiResult ? 'ANFIS-powered classification' : 'Basic quality assessment'}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {renderAIResults()}
        {renderLegacyResults()}
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowDetails(!showDetails)}
          className="w-full"
        >
          <Info className="w-4 h-4 mr-2" />
          {showDetails ? 'Hide Details' : 'Show Details'}
        </Button>

        <div className="text-xs text-muted-foreground text-center p-2 bg-muted rounded">
          <div className="flex items-center justify-center gap-1 mb-1">
            <TrendingUp className="w-3 h-3" />
            <span>ANFIS Model Performance</span>
          </div>
          <div className="text-center">
            <div className="font-medium">ANFIS Model</div>
            <div className="text-green-600">High Accuracy</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}; 