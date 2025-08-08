import { useState } from "react";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import Logo from '/LOGO.png';

export const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="bg-[#2e191e] shadow-material-sm backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8">
        <div className="flex justify-between items-center h-14 sm:h-16">
          {/* Logo Only */}
          <div className="flex items-center">
            <div className="w-32 sm:w-40 h-auto flex items-center justify-center">
              <img src={Logo} alt="Pepper Vision Logo" className="w-40 sm:w-56 h-auto object-contain" />
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-4 sm:space-x-8">
            <a
              href="#home"
              className="text-emphasis hover:text-primary transition-colors duration-200 font-medium relative group"
            >
              Home
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-200 group-hover:w-full"></span>
            </a>
            <a
              href="#about"
              className="text-subtle hover:text-primary transition-colors duration-200 font-medium relative group"
            >
              About
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-200 group-hover:w-full"></span>
            </a>
            <a
              href="#dataset"
              className="text-subtle hover:text-primary transition-colors duration-200 font-medium relative group"
            >
              Dataset
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-200 group-hover:w-full"></span>
            </a>
            <a
              href="#contact"
              className="text-subtle hover:text-primary transition-colors duration-200 font-medium relative group"
            >
              Contact
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all duration-200 group-hover:w-full"></span>
            </a>
          </nav>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden hover:bg-primary/5"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-5 w-5 icon-primary" /> : <Menu className="h-5 w-5 icon-primary" />}
          </Button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden pb-4 animate-fade-in">
            <nav className="flex flex-col space-y-2">
              <a
                href="#home"
                className="text-emphasis hover:text-primary transition-colors duration-200 font-medium py-2 px-3 rounded-lg hover:bg-primary/5"
                onClick={() => setIsMenuOpen(false)}
              >
                Home
              </a>
              <a
                href="#about"
                className="text-subtle hover:text-primary transition-colors duration-200 font-medium py-2 px-3 rounded-lg hover:bg-primary/5"
                onClick={() => setIsMenuOpen(false)}
              >
                About
              </a>
              <a
                href="#dataset"
                className="text-subtle hover:text-primary transition-colors duration-200 font-medium py-2 px-3 rounded-lg hover:bg-primary/5"
                onClick={() => setIsMenuOpen(false)}
              >
                Dataset
              </a>
              <a
                href="#contact"
                className="text-subtle hover:text-primary transition-colors duration-200 font-medium py-2 px-3 rounded-lg hover:bg-primary/5"
                onClick={() => setIsMenuOpen(false)}
              >
                Contact
              </a>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};