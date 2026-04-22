// src/App.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Navbar from "./components/Navbar"
import Dashboard from "./pages/Dashboard"
import TickerView from "./pages/TickerView"
import "./index.css"

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/ticker/:ticker" element={<TickerView />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}