import Dashboard from "./pages/Dashboard";
import { Toaster} from "./components/ui/toast";
import { LanguageProvider } from "./context/LanguageContext";



function App() {
  return (
    <LanguageProvider>
  <Dashboard />
  <Toaster />
</LanguageProvider>
  );
}

export default App;