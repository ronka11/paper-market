// src/App.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Navbar from "./components/Navbar"
import Dashboard from "./pages/Dashboard"
import TickerView from "./pages/TickerView"
import WelcomeModal from "./components/WelcomeModal"
import Compare from "./pages/Compare"
import "./index.css"

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <WelcomeModal />
      <main className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/ticker/:ticker" element={<TickerView />} />
          <Route path="/compare" element={<Compare />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}