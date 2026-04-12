export default function HeroSection() {
  return (
    <section className="bg-gradient-to-r from-red-600 via-red-500 to-pink-500 rounded-2xl shadow-2xl overflow-hidden mb-8">
      <div className="max-w-7xl mx-auto px-6 py-16 md:py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="text-white space-y-6">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
              Save Lives.
              <br />
              <span className="text-yellow-300">Donate Blood.</span>
            </h1>
            <p className="text-lg md:text-xl text-red-100 max-w-lg">
              Join thousands of heroes saving lives every day. Your single donation can save up to 3 lives.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <button className="bg-white text-red-600 hover:bg-gray-100 px-8 py-4 rounded-xl font-bold text-lg shadow-xl hover:shadow-2xl transition-all transform hover:-translate-y-1 flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Request Blood
              </button>
              <button className="border-2 border-white text-white hover:bg-white/10 px-8 py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                Become a Donor
              </button>
            </div>
          </div>

          {/* Right - Illustration */}
          <div className="hidden md:flex justify-center">
            <div className="relative">
              <div className="w-80 h-80 bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center">
                <svg className="w-48 h-48 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 2a6 6 0 00-6 6c0 3.314 2.686 6 6 6s6-2.686 6-6a6 6 0 00-6-6zm0 10a4 4 0 110-8 4 4 0 010 8z"/>
                </svg>
              </div>
              {/* Floating elements */}
              <div className="absolute -top-4 -right-4 bg-yellow-400 text-red-700 px-4 py-2 rounded-lg font-bold shadow-lg animate-bounce">
                Save 3 Lives!
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
