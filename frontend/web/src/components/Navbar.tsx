import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-red-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2a6 6 0 00-6 6c0 3.314 2.686 6 6 6s6-2.686 6-6a6 6 0 00-6-6zm0 10a4 4 0 110-8 4 4 0 010 8z"/>
              </svg>
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-red-600 to-red-500 bg-clip-text text-transparent">
              BloodLife
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/" className="text-gray-700 hover:text-red-600 font-medium transition-colors">
              Home
            </Link>
            <Link to="/requests" className="text-gray-700 hover:text-red-600 font-medium transition-colors">
              Live Requests
            </Link>
            <Link to="/donors" className="text-gray-700 hover:text-red-600 font-medium transition-colors">
              Find Donors
            </Link>
            <Link to="/track" className="text-gray-700 hover:text-red-600 font-medium transition-colors">
              Track Request
            </Link>
          </div>

          {/* Auth Buttons */}
          <div className="flex items-center space-x-4">
            <Link to="/login" className="text-gray-700 hover:text-red-600 font-medium transition-colors">
              Login
            </Link>
            <button className="bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 text-white px-6 py-2 rounded-lg font-semibold shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5">
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
