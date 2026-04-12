import { useState, useEffect } from 'react'
import axios from 'axios'
import Navbar from './components/Navbar'
import HeroSection from './components/HeroSection'
import StatsSection from './components/StatsSection'
import LiveRequestsSection from './components/LiveRequestsSection'
import QuickActionsSection from './components/QuickActionsSection'
import DonorSearchSection from './components/DonorSearchSection'
import RequestTrackerSection from './components/RequestTrackerSection'
import Footer from './components/Footer'

interface Stats {
  lives_saved: number
  donors_joined: number
  requests_fulfilled: number
  active_requests: number
}

function App() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/v2/dashboard/stats/')
      if (response.data.success) {
        setStats(response.data.stats)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f5f7fa] to-[#c3cfe2]">
      <Navbar />
      
      <main className="container mx-auto px-4 py-8">
        <HeroSection />
        
        <StatsSection stats={stats} loading={loading} />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
          <LiveRequestsSection />
          <QuickActionsSection />
        </div>
        
        <DonorSearchSection />
        
        <RequestTrackerSection />
      </main>
      
      <Footer />
    </div>
  )
}

export default App
