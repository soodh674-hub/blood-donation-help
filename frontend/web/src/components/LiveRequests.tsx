import { useEffect, useState } from 'react'
import axios from 'axios'

interface Request {
  id: number
  patient_blood_group: string
  priority: string
  hospital_name: string
  city: string
  created_at: string
}

export default function LiveRequests() {
  const [requests, setRequests] = useState<Request[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLiveRequests()
  }, [])

  const fetchLiveRequests = async () => {
    try {
      const response = await axios.get('/api/v2/requests/live/?limit=5')
      if (response.data.success) {
        setRequests(response.data.requests)
      }
    } catch (error) {
      console.error('Error fetching live requests:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-dark-800 p-5 rounded-xl shadow">
        <h2 className="text-xl mb-4">Live Blood Requests</h2>
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  return (
    <div className="bg-dark-800 p-5 rounded-xl shadow">
      <h2 className="text-xl font-bold mb-4">Live Blood Requests</h2>

      {requests.length === 0 ? (
        <p className="text-gray-400">No active requests at the moment</p>
      ) : (
        <div className="space-y-3">
          {requests.map((request) => (
            <div key={request.id} className="bg-dark-700 p-4 rounded-lg flex justify-between items-start hover:bg-dark-600 transition-colors">
              <div>
                <span className={`px-2 py-1 text-xs rounded ${
                  request.priority === 'urgent' ? 'bg-red-500' : 'bg-orange-500'
                }`}>
                  {request.priority.toUpperCase()}
                </span>
                <h3 className="mt-2 font-bold">{request.patient_blood_group} Blood needed</h3>
                <p className="text-gray-400 text-sm">
                  {request.hospital_name} • {request.city}
                </p>
              </div>

              <button className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded text-sm font-semibold transition-colors">
                Donate Now
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
