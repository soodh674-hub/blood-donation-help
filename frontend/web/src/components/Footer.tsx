import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-red-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a6 6 0 00-6 6c0 3.314 2.686 6 6 6s6-2.686 6-6a6 6 0 00-6-6zm0 10a4 4 0 110-8 4 4 0 010 8z"/>
                </svg>
              </div>
              <span className="text-2xl font-bold">BloodLife</span>
            </div>
            <p className="text-gray-400 text-sm">
              Saving lives through blood donation. Connect donors with those in need.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-lg mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li><Link to="/" className="text-gray-400 hover:text-red-400 transition-colors">Home</Link></li>
              <li><Link to="/requests" className="text-gray-400 hover:text-red-400 transition-colors">Live Requests</Link></li>
              <li><Link to="/donors" className="text-gray-400 hover:text-red-400 transition-colors">Find Donors</Link></li>
              <li><Link to="/track" className="text-gray-400 hover:text-red-400 transition-colors">Track Request</Link></li>
            </ul>
          </div>

          {/* For Donors */}
          <div>
            <h3 className="font-semibold text-lg mb-4">For Donors</h3>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-red-400 transition-colors">How to Donate</a></li>
              <li><a href="#" className="text-gray-400 hover:text-red-400 transition-colors">Eligibility Criteria</a></li>
              <li><a href="#" className="text-gray-400 hover:text-red-400 transition-colors">Donation Centers</a></li>
              <li><a href="#" className="text-gray-400 hover:text-red-400 transition-colors">FAQs</a></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="font-semibold text-lg mb-4">Contact Us</h3>
            <ul className="space-y-2 text-gray-400">
              <li>Email: support@bloodlife.com</li>
              <li>Phone: +1 (555) 123-4567</li>
              <li>Emergency: 24/7 Hotline</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
          <p>&copy; 2026 BloodLife. All rights reserved. Made with ❤️ to save lives.</p>
        </div>
      </div>
    </footer>
  )
}
