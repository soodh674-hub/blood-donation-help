import { useState } from 'react'

export default function RequestTrackerSection() {
  const [requestId, setRequestId] = useState('')

  return (
    <section className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 mt-8 border-2 border-blue-100">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        Track Your Blood Request
      </h2>

      <div className="flex gap-4 mb-6">
        <input
          type="text"
          value={requestId}
          onChange={(e) => setRequestId(e.target.value)}
          placeholder="Enter Request ID (e.g., REQ-2026-001)"
          className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
        />
        <button className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white px-8 py-3 rounded-lg font-semibold shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5">
          Track
        </button>
      </div>

      {/* Sample Tracking Info */}
      <div className="bg-white rounded-lg p-6 border-2 border-blue-100">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-800 text-lg">Request #REQ-2026-001</h3>
            <p className="text-sm text-gray-600">Patient: John Doe • O+ • 2 units</p>
          </div>
          <span className="bg-yellow-100 text-yellow-700 px-4 py-2 rounded-full text-sm font-semibold">
            In Progress
          </span>
        </div>

        {/* Timeline */}
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
          
          <div className="space-y-6">
            <div className="flex items-start gap-4 relative">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center z-10">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="flex-1 bg-green-50 p-3 rounded-lg">
                <p className="font-medium text-gray-800">Request Created</p>
                <p className="text-sm text-gray-600">April 4, 2026 at 10:30 AM</p>
              </div>
            </div>

            <div className="flex items-start gap-4 relative">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center z-10">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="flex-1 bg-green-50 p-3 rounded-lg">
                <p className="font-medium text-gray-800">Donors Notified</p>
                <p className="text-sm text-gray-600">April 4, 2026 at 10:32 AM • 15 donors contacted</p>
              </div>
            </div>

            <div className="flex items-start gap-4 relative">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center z-10 animate-pulse">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1 bg-blue-50 p-3 rounded-lg border-2 border-blue-200">
                <p className="font-medium text-gray-800">Matching Donors Found</p>
                <p className="text-sm text-gray-600">Currently searching for available donors...</p>
              </div>
            </div>

            <div className="flex items-start gap-4 relative opacity-50">
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center z-10">
                <span className="text-white text-sm">4</span>
              </div>
              <div className="flex-1 bg-gray-50 p-3 rounded-lg">
                <p className="font-medium text-gray-600">Request Fulfilled</p>
                <p className="text-sm text-gray-500">Pending</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
