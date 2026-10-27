import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { AUTH_DISABLED, msalConfig, variablesFaltantes } from "./authConfig";
import App from "./App.jsx";
import ConfigError from "./components/ConfigError.jsx";

const raiz = createRoot(document.getElementById("root"));

async function iniciar() {
  if (variablesFaltantes.length > 0) {
    raiz.render(<ConfigError faltantes={variablesFaltantes} />);
    return;
  }

  if (AUTH_DISABLED) {
    raiz.render(
      <StrictMode>
        <App />
      </StrictMode>
    );
    return;
  }

  const msalInstance = new PublicClientApplication(msalConfig);
  await msalInstance.initialize();
  raiz.render(
    <StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </StrictMode>
  );
}

iniciar();
