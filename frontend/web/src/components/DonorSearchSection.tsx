import { useState } from 'react'

export default function DonorSearchSection() {
  const [bloodGroup, setBloodGroup] = useState('')
  const [city, setCity] = useState('')

  const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

  return (
    <section className="bg-white rounded-xl shadow-lg p-6 mt-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        Find Donors Near You
      </h2>

      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Blood Group</label>
          <select
            value={bloodGroup}
            onChange={(e) => setBloodGroup(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200 transition-all"
          >
            <option value="">Select Blood Group</option>
            {bloodGroups.map(group => (
              <option key={group} value={group}>{group}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">City/Location</label>
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter your city"
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-red-500 focus:ring-2 focus:ring-red-200 transition-all"
          />
        </div>

        <div className="flex items-end">
          <button className="w-full bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 text-white px-6 py-3 rounded-lg font-semibold shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5">
            Search Donors
          </button>
        </div>
      </div>

      {/* Sample Results */}
      <div className="space-y-3">
        <p className="text-sm text-gray-600 mb-4">Showing available donors in your area</p>
        
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between p-4 border-2 border-gray-100 rounded-lg hover:border-red-200 hover:bg-red-50 transition-all">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                D{i}
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Donor Name {i}</h4>
                <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                  <span className="bg-red-100 text-red-700 px-2 py-1 rounded font-bold">O+</span>
                  <span>• 2.5 km away</span>
                  <span>• Last donated: 45 days ago</span>
                </div>
              </div>
            </div>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
              View Profile
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}
