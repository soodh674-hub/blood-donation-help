import { useState, useEffect } from 'react'
import axios from 'axios'

interface Request {
  id: number
  patient_name: string
  blood_group: string
  units_needed: number
  hospital_name: string
  city: string
  urgency_level: string
  created_at: string
}

export default function LiveRequestsSection() {
  const [requests, setRequests] = useState<Request[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRequests()
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchRequests, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchRequests = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/v2/requests/live/')
      if (response.data.success) {
        setRequests(response.data.requests)
      }
    } catch (error) {
      console.error('Error fetching requests:', error)
    } finally {
      setLoading(false)
    }
  }

  const getUrgencyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-300'
      case 'urgent': return 'bg-orange-100 text-orange-700 border-orange-300'
      case 'moderate': return 'bg-yellow-100 text-yellow-700 border-yellow-300'
      default: return 'bg-blue-100 text-blue-700 border-blue-300'
    }
  }

  if (loading && requests.length === 0) {
    return (
      <section className="bg-white rounded-xl shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-100 rounded"></div>
          ))}
        </div>
      </section>
    )
  }

  return (
    <section className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
          Live Blood Requests
        </h2>
        <button 
          onClick={fetchRequests}
          className="text-sm text-red-600 hover:text-red-700 font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-4 max-h-96 overflow-y-auto">
        {requests.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No active requests at the moment
          </div>
        ) : (
          requests.map((request) => (
            <div key={request.id} className="border-l-4 border-red-500 bg-gradient-to-r from-red-50 to-white p-4 rounded-lg hover:shadow-md transition-all">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-semibold text-gray-800">{request.patient_name}</h3>
                  <p className="text-sm text-gray-600">{request.hospital_name}, {request.city}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getUrgencyColor(request.urgency_level)}`}>
                  {request.urgency_level.toUpperCase()}
                </span>
              </div>
              
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-4">
                  <div className="bg-red-100 text-red-700 px-3 py-1 rounded-lg font-bold">
                    {request.blood_group}
                  </div>
                  <span className="text-sm text-gray-600">
                    {request.units_needed} unit{request.units_needed > 1 ? 's' : ''} needed
                  </span>
                </div>
                <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
                  Donate Now
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  )
}
