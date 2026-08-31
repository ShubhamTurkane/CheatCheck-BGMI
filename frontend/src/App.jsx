import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Landing from "./pages/Landing";
import Analyze from "./pages/Analyze";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <div className="min-h-screen text-ink">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
