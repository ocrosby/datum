import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Rankings from './pages/Rankings';
import Conferences from './pages/Conferences';
import ConferenceDetails from './pages/ConferenceDetails';
import TeamDetails from './pages/TeamDetails';
import Matches from './pages/Matches';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import { RPIProvider } from './contexts/RPIContext';
import PerformanceMonitor from './components/PerformanceMonitor';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RPIProvider>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Navbar />
            <main className="pt-16">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/rankings" element={<Rankings />} />
                <Route path="/conferences" element={<Conferences />} />
                <Route path="/conferences/:conference" element={<ConferenceDetails />} />
                <Route path="/team/:teamId" element={<TeamDetails />} />
                <Route path="/matches" element={<Matches />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10B981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#EF4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
            <PerformanceMonitor />
          </div>
        </Router>
      </RPIProvider>
    </QueryClientProvider>
  );
}

export default App; 