import { useState } from "react";
import { Image as ImageIcon, Clock, Star, TrendingUp, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SampleImagesProps {
  onSampleSelect: (imageUrl: string) => void;
}

export const SampleImages = ({ onSampleSelect }: SampleImagesProps) => {
  const [selectedSample, setSelectedSample] = useState<string | null>(null);

  // Mock sample images - using SVG placeholders to avoid CORS issues
  const sampleImages = [
    {
      id: 'sample1',
      url: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZGMzNjI2Ii8+Cjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2Ij5HcmFkZSBBIFJlZCBQZXBwZXI8L3RleHQ+Cjwvc3ZnPg==',
      name: 'Grade A Red Pepper',
      description: 'Perfect specimen',
      grade: 'Grade A'
    },
    {
      id: 'sample2', 
      url: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZWFiMzA4Ii8+Cjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2Ij5HcmFkZSBCIFllbGxvdyBQZXBwZXI8L3RleHQ+Cjwvc3ZnPg==',
      name: 'Grade B Yellow Pepper',
      description: 'Minor blemishes',
      grade: 'Grade B'
    },
    {
      id: 'sample3',
      url: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMTY4MDNkIi8+Cjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSJ3aGl0ZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2Ij5HcmFkZSBDIEdyZWVuIFBlcHBlcjwvdGV4dD4KPHN2Zz4=',
      name: 'Grade C Green Pepper',
      description: 'Visible defects',
      grade: 'Grade C'
    }
  ];

  // Mock recent results
  const recentResults = [
    {
      id: 'recent1',
      grade: 'Grade A',
      confidence: 95,
      timestamp: '2 minutes ago'
    },
    {
      id: 'recent2',
      grade: 'Grade B',
      confidence: 87,
      timestamp: '15 minutes ago'
    },
    {
      id: 'recent3',
      grade: 'Grade A',
      confidence: 92,
      timestamp: '1 hour ago'
    }
  ];

  const handleSampleClick = (imageUrl: string, id: string) => {
    setSelectedSample(id);
    onSampleSelect(imageUrl);
  };

  const getGradeColor = (grade: string) => {
    switch (grade.toLowerCase()) {
      case 'grade a':
        return 'bg-success';
      case 'grade b':
        return 'bg-accent';
      case 'grade c':
        return 'bg-warning';
      default:
        return 'bg-destructive';
    }
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 90) return <Star className="w-3 h-3 text-success" />;
    if (confidence >= 70) return <TrendingUp className="w-3 h-3 text-accent" />;
    return <AlertCircle className="w-3 h-3 text-warning" />;
  };

  return (
    <div className="space-y-6">
      {/* Sample Images */}
      <div>
        <h3 className="text-base sm:text-lg font-semibold text-emphasis mb-4 flex items-center gap-2">
          <ImageIcon className="w-5 h-5 icon-primary" />
          Sample Images
        </h3>
        <div id="sampleImages" className="space-y-3">
          {sampleImages.map((sample) => (
            <div
              key={sample.id}
              className={`card-material p-2 sm:p-3 cursor-pointer transition-all duration-200 hover:shadow-material-lg ${
                selectedSample === sample.id ? 'border-primary bg-primary/5' : ''
              }`}
              onClick={() => handleSampleClick(sample.url, sample.id)}
            >
              <div className="flex gap-2 sm:gap-3">
                <div className="relative">
                  <img
                    src={sample.url}
                    alt={sample.name}
                    className="w-12 h-12 sm:w-16 sm:h-16 rounded-lg object-cover"
                  />
                  <div className={`absolute -top-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 rounded-full ${getGradeColor(sample.grade)} border-2 border-card`}></div>
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-emphasis text-xs sm:text-sm truncate">
                    {sample.name}
                  </h4>
                  <p className="text-xs text-subtle mt-1">
                    {sample.description}
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-2 h-7 text-xs hover:bg-primary/5"
                  >
                    Use Sample
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Results */}
      <div>
        <h3 className="text-base sm:text-lg font-semibold text-emphasis mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 icon-primary" />
          Recent Analyses
        </h3>
        <div id="recentResults" className="space-y-2 sm:space-y-3">
          {recentResults.map((result) => (
            <div
              key={result.id}
              className="card-material p-2 sm:p-3 hover:shadow-material-lg transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-1 sm:gap-2">
                    <div className={`w-2 h-2 rounded-full ${getGradeColor(result.grade)}`}></div>
                    <span className="font-medium text-emphasis text-xs sm:text-sm">
                      {result.grade}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 mt-1">
                    {getConfidenceIcon(result.confidence)}
                    <p className="text-xs text-subtle">
                      {result.confidence}% confidence
                    </p>
                  </div>
                </div>
                <span className="text-xs text-subtle">
                  {result.timestamp}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};