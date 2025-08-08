import { useRef, useState } from "react";
import { Scissors } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RegionSelectorProps {
  imageUrl: string | null;
  imageFile: File | null;
  onAnalysisResult: (result: any) => void;
  onAnalysisStart: () => void;
}

export const RegionSelector = ({ imageUrl, imageFile, onAnalysisResult, onAnalysisStart }: RegionSelectorProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [croppedImageUrl, setCroppedImageUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [detectedBoxes, setDetectedBoxes] = useState<Array<[number, number, number, number]>>([]);
  const [imgDims, setImgDims] = useState<{naturalWidth: number, naturalHeight: number, clientWidth: number, clientHeight: number}>({naturalWidth: 1, naturalHeight: 1, clientWidth: 1, clientHeight: 1});

  const handleImageClick = async (e: React.MouseEvent) => {
    if (!containerRef.current || !imgRef.current || !imageFile) return;
    const rect = imgRef.current.getBoundingClientRect();
    // Calculate scaling factors
    const scaleX = imgRef.current.naturalWidth / imgRef.current.clientWidth;
    const scaleY = imgRef.current.naturalHeight / imgRef.current.clientHeight;
    // Get click position relative to image
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);
    setIsLoading(true);
    setAnalysis(null);
    setCroppedImageUrl(null);
    onAnalysisStart(); // Notify parent that analysis is starting
    // Prepare form data
    const formData = new FormData();
    formData.append("image", imageFile);
    formData.append("click_x", x.toString());
    formData.append("click_y", y.toString());
    // Send to backend
    try {
      // Use environment variable for backend URL
      const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      console.log('API URL:', apiUrl);
      
      // Add cache busting to prevent caching issues
      const cacheBuster = `_cb=${Date.now()}`;
      const fullUrl = `${apiUrl}/select-object?${cacheBuster}`;
      console.log('Full URL:', fullUrl);
      
      const res = await fetch(fullUrl, {
        method: "POST",
        body: formData,
        cache: 'no-store', // Prevent caching
      });
      if (!res.ok) {
        let errorMsg = "No object detected at the selected location.";
        console.error(`API error: ${res.status} ${res.statusText}`);
        try {
          const errorData = await res.text();
          console.error('Error response:', errorData);
        } catch (textError) {
          console.error('Could not read error response text');
        }
        try {
          const errorData = await res.json();
          errorMsg = errorData.error || errorMsg;
          if (errorData.boxes) setDetectedBoxes(errorData.boxes);
        } catch {}
        alert(errorMsg);
        setIsLoading(false);
        return;
      }
      const data = await res.json();
      if (data.boxes) setDetectedBoxes(data.boxes);
      setIsLoading(false);
      if (data.cropped_image) {
        const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        setCroppedImageUrl(`${apiUrl}${data.cropped_image}`);
      }
      setAnalysis(data);
      onAnalysisResult(data);
    } catch (err) {
      alert("Failed to connect to backend or unexpected error occurred.");
      setIsLoading(false);
    }
  };

  const handleImgLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImgDims({
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      clientWidth: img.clientWidth,
      clientHeight: img.clientHeight,
    });
  };

  if (!imageUrl) return null;

  // Calculate scaling factors for drawing boxes
  const scaleX = imgDims.clientWidth / imgDims.naturalWidth;
  const scaleY = imgDims.clientHeight / imgDims.naturalHeight;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-emphasis">Select Object for Analysis</h3>
          <p className="text-sm text-subtle">
            Click on the object you want to analyze
          </p>
        </div>
      </div>
      <div
        ref={containerRef}
        className="relative inline-block cursor-pointer"
        style={{ pointerEvents: isLoading ? "none" : "auto" }}
      >
        <img
          ref={imgRef}
          src={imageUrl}
          alt="Bell pepper for object selection"
          className="max-w-full h-auto rounded-lg shadow-material-lg"
          draggable={false}
          onLoad={handleImgLoad}
        />
        {/* Draw detected bounding boxes */}
        {detectedBoxes.map((box, i) => {
          const [x1, y1, x2, y2] = box;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x1 * scaleX,
                top: y1 * scaleY,
                width: (x2 - x1) * scaleX,
                height: (y2 - y1) * scaleY,
                border: "2px solid #00FF00",
                boxSizing: "border-box",
                pointerEvents: "none",
                zIndex: 20,
              }}
            />
          );
        })}
        {/* Overlay for click events */}
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            width: imgDims.clientWidth,
            height: imgDims.clientHeight,
            zIndex: 10,
          }}
          onClick={handleImageClick}
        />
        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 rounded-lg">
            <div className="bg-card p-4 rounded-lg shadow-material-lg text-center border border-border">
              <Scissors className="w-8 h-8 icon-success mx-auto mb-2 animate-spin" />
              <p className="text-sm font-medium text-emphasis">Analyzing...</p>
            </div>
          </div>
        )}
      </div>
      {/* Show cropped image and analysis */}
      {croppedImageUrl && (
        <div className="mt-4 text-center">
          <h4 className="font-semibold mb-2">Detected Object</h4>
          <img src={croppedImageUrl} alt="Cropped object" className="inline-block rounded shadow-lg max-w-xs" />
        </div>
      )}

    </div>
  );
};