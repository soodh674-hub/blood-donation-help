export default function QuickActionsSection() {
  const actions = [
    {
      title: 'Create Blood Request',
      description: 'Request blood for a patient in need',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      ),
      color: 'from-red-500 to-red-600',
      href: '/requests/create'
    },
    {
      title: 'Find Donors Near You',
      description: 'Search for available donors in your area',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      color: 'from-blue-500 to-blue-600',
      href: '/donors/search'
    },
    {
      title: 'Track Your Request',
      description: 'Monitor the status of your blood request',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      ),
      color: 'from-green-500 to-green-600',
      href: '/track'
    },
    {
      title: 'Update Donor Status',
      description: 'Mark yourself as available or unavailable',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
      color: 'from-purple-500 to-purple-600',
      href: '/profile/update-status'
    }
  ]

  return (
    <section className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Quick Actions</h2>
      
      <div className="grid grid-cols-1 gap-4">
        {actions.map((action, index) => (
          <a
            key={index}
            href={action.href}
            className="group flex items-start gap-4 p-4 rounded-lg border-2 border-gray-100 hover:border-red-200 hover:bg-red-50 transition-all"
          >
            <div className={`bg-gradient-to-br ${action.color} text-white p-3 rounded-lg group-hover:scale-110 transition-transform`}>
              {action.icon}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-800 group-hover:text-red-600 transition-colors">
                {action.title}
              </h3>
              <p className="text-sm text-gray-600 mt-1">{action.description}</p>
            </div>
            <svg className="w-5 h-5 text-gray-400 group-hover:text-red-600 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </a>
        ))}
      </div>
    </section>
  )
}
