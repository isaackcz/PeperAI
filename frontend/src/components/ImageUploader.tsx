import { useState, useRef } from "react";
import { Upload, Camera, RotateCcw, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";

interface ImageUploaderProps {
  onImageSelect: (image: File | null) => void;
  selectedImage: File | null;
}

export const ImageUploader = ({ onImageSelect, selectedImage }: ImageUploaderProps) => {
  const [dragActive, setDragActive] = useState(false);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [cameraActive, setCameraActive] = useState(false);

  const handleFileSelect = (file: File) => {
    if (file && file.type.startsWith('image/')) {
      onImageSelect(file);
      const url = URL.createObjectURL(file);
      setImagePreviewUrl(url);
      toast({
        title: "Image uploaded successfully",
        description: "Ready for analysis",
      });
    } else {
      toast({
        title: "Invalid file type",
        description: "Please select an image file",
        variant: "destructive",
      });
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment' // Prefer back camera
        } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
        toast({
          title: "Camera activated",
          description: "Position your bell pepper and click capture",
        });
      }
    } catch (error) {
      toast({
        title: "Camera access denied",
        description: "Please allow camera access or upload an image instead",
        variant: "destructive",
      });
    }
  };

  const captureImage = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      ctx?.drawImage(video, 0, 0);
      
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], 'captured-image.jpg', { type: 'image/jpeg' });
          handleFileSelect(file);
          stopCamera();
        }
      }, 'image/jpeg', 0.8);
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
    }
    setCameraActive(false);
  };

  const resetImage = () => {
    onImageSelect(null);
    setImagePreviewUrl(null);
    if (imagePreviewUrl) {
      URL.revokeObjectURL(imagePreviewUrl);
    }
  };

  return (
    <div className="flex justify-center items-center w-full min-h-[220px] sm:min-h-[320px] relative">
      <div className="relative z-10 w-full max-w-xs sm:max-w-md md:max-w-lg flex flex-col justify-center items-center">
        <div
          className="w-full bg-gradient-to-br from-white/10 via-background to-white/5 border-2 border-dashed border-border rounded-xl flex flex-col items-center justify-center py-12 px-4 sm:px-10 shadow-lg transition-all duration-200 hover:border-primary focus-within:border-primary"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={!imagePreviewUrl ? openFileDialog : undefined}
          style={{ cursor: !imagePreviewUrl ? 'pointer' : 'default' }}
        >
          {!imagePreviewUrl ? (
            <>
              <div className="flex flex-col items-center justify-center mb-2">
                <div className="bg-primary/10 rounded-full p-5 mb-4">
                  <ImageIcon className="w-14 h-14 text-primary" />
                </div>
                <h3 className="text-xl font-semibold text-emphasis mb-1">Choose files or drag them here</h3>
                <p className="text-subtle mb-2 text-base">Accepted formats: <span className="font-semibold">JPG, PNG</span>. Max file size: <span className="font-semibold">5MB</span> each.</p>
              </div>
            </>
          ) : (
            <div className="text-center">
              <div className="relative inline-block mb-4">
                <img
                  id="imagePreview"
                  src={imagePreviewUrl}
                  alt="Uploaded bell pepper"
                  className="max-w-full max-h-48 sm:max-h-96 rounded-lg shadow-material-lg"
                />
              </div>
              <div className="flex gap-2 sm:gap-3 justify-center">
                <Button
                  onClick={resetImage}
                  variant="outline"
                  className="ripple hover:bg-primary/5"
                >
                  <RotateCcw className="w-4 h-4 mr-2 icon-primary" />
                  Upload Different Image
                </Button>
              </div>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileSelect(file);
            }}
            className="hidden"
          />
        </div>
        {/* Camera button below everything */}
        {!imagePreviewUrl && (
          <div className="mt-5 flex justify-center w-full">
            <Button
              id="captureBtn"
              onClick={startCamera}
              className="btn-accent ripple w-full sm:w-auto shadow-md"
            >
              <Camera className="w-4 h-4 mr-2" />
              Capture Image
            </Button>
          </div>
        )}
        {/* Camera view below upload input */}
        {cameraActive && (
          <div className="card-material animate-fade-in mt-6 w-full flex flex-col items-center justify-center">
            <div className="text-center w-full">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full max-w-xs sm:max-w-md mx-auto rounded-lg mb-4 border border-primary"
              />
              <canvas ref={canvasRef} className="hidden" />
              <div className="flex gap-2 justify-center">
                <Button
                  onClick={captureImage}
                  className="btn-success ripple"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Capture
                </Button>
                <Button
                  onClick={stopCamera}
                  variant="outline"
                  className="ripple hover:bg-destructive/5 border-destructive text-destructive hover:text-destructive-foreground"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};