interface Stats {
  lives_saved: number
  donors_joined: number
  requests_fulfilled: number
  active_requests: number
}

interface Props {
  stats: Stats | null
  loading: boolean
}

export default function StatsSection({ stats, loading }: Props) {
  if (loading) {
    return (
      <section className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </section>
    )
  }

  if (!stats) return null

  const statCards = [
    { label: 'Lives Saved', value: stats.lives_saved, color: 'from-red-500 to-red-600', icon: '❤️' },
    { label: 'Donors Joined', value: stats.donors_joined, color: 'from-blue-500 to-blue-600', icon: '👥' },
    { label: 'Requests Fulfilled', value: stats.requests_fulfilled, color: 'from-green-500 to-green-600', icon: '✅' },
    { label: 'Active Requests', value: stats.active_requests, color: 'from-yellow-500 to-orange-500', icon: '🔴' },
  ]

  return (
    <section className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
      {statCards.map((stat, index) => (
        <div key={index} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1 overflow-hidden">
          <div className={`bg-gradient-to-r ${stat.color} p-4`}>
            <div className="text-4xl mb-2">{stat.icon}</div>
          </div>
          <div className="p-6">
            <h3 className="text-3xl font-bold text-gray-800 mb-1">
              {stat.value.toLocaleString()}
            </h3>
            <p className="text-gray-600 font-medium">{stat.label}</p>
          </div>
        </div>
      ))}
    </section>
  )
}
