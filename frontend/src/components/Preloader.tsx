import { useEffect, useState } from "react";
import Logo from "/LOGO.png";

export const Preloader = ({ onFinish }: { onFinish: () => void }) => {
  const [show, setShow] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShow(false);
      onFinish();
    }, 2200); // 2.2s preloader
    return () => clearTimeout(timer);
  }, [onFinish]);

  return show ? (
    <div className="preloader-bg">
      <div className="preloader-center">
        <img
          src={Logo}
          alt="Pepper Vision Logo"
          className="preloader-logo w-68 h-auto sm:w-64"
        />
        <h1 className="preloader-title">Pepper Vision Grade</h1>
      </div>
    </div>
  ) : null;
};
