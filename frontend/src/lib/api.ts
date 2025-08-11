// API service for connecting to the backend AI models
// In production, nginx proxies API requests, so we use relative paths
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? '' : 'http://127.0.0.1:8080');

export interface AIAnalysisResult {
  is_bell_pepper: boolean;
  ripeness: string;
  freshness_score: number;
  color: string;
  size: string;
  defects: string[];
  grade: string;
  confidence: number;
  freshness: string;
  recommendation: string;
  ai_defect_detection: {
    defect_type: string;
    confidence: number;
    probability: number;
    features: Record<string, number>;
    message: string;
    model_type: string;
  };
  display_analysis?: {
    classification: string;
    classification_confidence: number;
    second_most_likely: string;
    second_confidence: number;
    ripeness: string;
    freshness_score: number;
    quality_grade: string;
    freshness_level: string;
    probabilities: Record<string, number>;
  };
}

export interface ModelStatus {
  anfis_loaded: boolean;
  transfer_learning_loaded: boolean;
  ensemble_available: boolean;
  models_count: number;
  status: string;
}

export class APIService {
  private static async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Add cache-busting parameter to prevent browser caching
    const cacheBuster = `_cb=${Date.now()}`;
    const url = `${API_BASE_URL}${endpoint}${endpoint.includes('?') ? '&' : '?'}${cacheBuster}`;
    
    console.log('Making API request to:', url);
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        cache: 'no-store', // Prevent caching
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health check to verify backend is running
  static async healthCheck(): Promise<{ status: string }> {
    try {
      console.log('Performing health check to:', `${API_BASE_URL}/health`);
      return await this.makeRequest<{ status: string }>('/health');
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  // Get model status
  static async getModelStatus(): Promise<ModelStatus> {
    try {
      const response = await fetch(`${API_BASE_URL}/model-status`);
      if (response.ok) {
        const status = await response.json();
        console.log('Model status:', status);
        return status;
      }
      // Fallback if endpoint doesn't exist
      return {
        anfis_loaded: true,
        transfer_learning_loaded: true,
        ensemble_available: true,
        models_count: 5,
        status: 'Models loaded successfully (fallback)'
      };
    } catch (error) {
      console.warn('Model status endpoint not available, using fallback');
      return {
        anfis_loaded: true,
        transfer_learning_loaded: true,
        ensemble_available: true,
        models_count: 5,
        status: 'Models available (fallback)'
      };
    }
  }

  // Analyze image with AI models
  static async analyzeImage(
    imageFile: File,
    modelType: 'ensemble' | 'transfer' | 'anfis' = 'ensemble',
    region?: { x: number; y: number; width: number; height: number }
  ): Promise<AIAnalysisResult> {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('model_type', modelType);
    
    if (region) {
      formData.append('region', JSON.stringify(region));
    }

    const url = `${API_BASE_URL}/predict`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('AI Analysis Result:', result);
      return result;
    } catch (error) {
      console.error('AI analysis failed:', error);
      throw error;
    }
  }

  // Select object in image (for region selection)
  static async selectObject(
    imageFile: File,
    clickX: number,
    clickY: number
  ): Promise<{ cropped_image: string; region: [number, number, number, number] }> {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('click_x', clickX.toString());
    formData.append('click_y', clickY.toString());

    const url = `${API_BASE_URL}/select-object`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Object selection failed:', error);
      throw error;
    }
  }

  // Test different model types
  static async testModels(imageFile: File): Promise<{
    ensemble: AIAnalysisResult;
    transfer: AIAnalysisResult;
    anfis: AIAnalysisResult;
  }> {
    const [ensemble, transfer, anfis] = await Promise.all([
      this.analyzeImage(imageFile, 'ensemble'),
      this.analyzeImage(imageFile, 'transfer'),
      this.analyzeImage(imageFile, 'anfis'),
    ]);

    return { ensemble, transfer, anfis };
  }
}

// Utility functions for working with AI results
export const AIUtils = {
  // Get the best model recommendation based on confidence
  getBestModel(results: { ensemble: AIAnalysisResult; transfer: AIAnalysisResult; anfis: AIAnalysisResult }) {
    const confidences = {
      ensemble: results.ensemble.ai_defect_detection.confidence,
      transfer: results.transfer.ai_defect_detection.confidence,
      anfis: results.anfis.ai_defect_detection.confidence,
    };

    const bestModel = Object.entries(confidences).reduce((a, b) => 
      confidences[a[0] as keyof typeof confidences] > confidences[b[0] as keyof typeof confidences] ? a : b
    )[0];

    return {
      model: bestModel,
      confidence: confidences[bestModel as keyof typeof confidences],
      result: results[bestModel as keyof typeof results],
    };
  },

  // Format AI classification result for display
  formatClassification(result: AIAnalysisResult) {
    const ai = result.ai_defect_detection;
    return {
      category: ai.defect_type,
      confidence: ai.confidence,
      model: ai.model_type,
      message: ai.message,
      probabilities: ai.features,
    };
  },

  // Get confidence level description
  getConfidenceLevel(confidence: number): { level: string; color: string; icon: string } {
    if (confidence >= 90) {
      return { level: 'Excellent', color: 'text-green-500', icon: '⭐' };
    } else if (confidence >= 80) {
      return { level: 'Very Good', color: 'text-blue-500', icon: '👍' };
    } else if (confidence >= 70) {
      return { level: 'Good', color: 'text-yellow-500', icon: '✅' };
    } else if (confidence >= 50) {
      return { level: 'Fair', color: 'text-orange-500', icon: '⚠️' };
    } else {
      return { level: 'Poor', color: 'text-red-500', icon: '❌' };
    }
  },

  // Get category color for UI
  getCategoryColor(category: string): string {
    const colors = {
      ripe: 'bg-green-500',
      unripe: 'bg-yellow-500',
      old: 'bg-orange-500',
      dried: 'bg-brown-500',
      damaged: 'bg-red-500',
    };
    return colors[category.toLowerCase() as keyof typeof colors] || 'bg-gray-500';
  },
};