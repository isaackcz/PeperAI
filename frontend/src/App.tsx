import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import { Preloader } from "@/components/Preloader";

const queryClient = new QueryClient();

const App = () => {
  const [loading, setLoading] = useState(true);
  const [showLogoAnim, setShowLogoAnim] = useState(false);

  const handlePreloaderFinish = () => {
    setShowLogoAnim(true);
    setTimeout(() => setLoading(false), 1000); // Show logo slide-up, then main page
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        {loading && <Preloader onFinish={handlePreloaderFinish} />}
        <div
          className={showLogoAnim ? "slide-up-logo" : ""}
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 0,
            zIndex: 100,
          }}
        >
          {/* Logo at top after slide-up, can be customized or removed if not needed */}
        </div>
        <div className={showLogoAnim ? "slide-up-main" : ""}>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </div>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
