import React, { useEffect } from "react";
import { AppProviders } from "./providers/AppProviders";

const App: React.FC = () => {
  useEffect(() => {
    // Signal to prerenderer that the page content is ready
    document.dispatchEvent(new Event("prerender-ready"));
  }, []);

  return <AppProviders />;
};

export default App;
