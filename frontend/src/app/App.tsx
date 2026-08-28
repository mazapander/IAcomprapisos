import { useEffect, useState } from 'react'

import { track } from '../api'
import SiteFooter from '../layout/SiteFooter'
import SiteHeader from '../layout/SiteHeader'
import ConsentBanner from '../shared/components/ConsentBanner'
import type { ToolId } from '../types'
import HomeView from '../views/HomeView'
import ToolView from '../views/ToolView'
import { useBuyerMarketContext } from './useBuyerMarketContext'

export default function App() {
  const [activeTool, setActiveTool] = useState<ToolId | null>(null)
  const [privacySignal, setPrivacySignal] = useState(0)
  const { geography, market, updateMarketContext } = useBuyerMarketContext()

  useEffect(() => { void track('page_view', { source: 'direct' }) }, [])

  function selectTool(id: ToolId) {
    setActiveTool(id)
    void track('tool_selected', { use_case: id })
    window.setTimeout(() => document.getElementById('workspace')?.scrollIntoView({ behavior: 'smooth' }), 0)
  }

  function showMethod() {
    setActiveTool(null)
    window.setTimeout(() => document.getElementById('method')?.scrollIntoView({ behavior: 'smooth' }), 0)
  }

  return (
    <div className="app-shell">
      <SiteHeader onSelect={selectTool} onHome={() => setActiveTool(null)} onMethod={showMethod} />
      <main>
        {activeTool
          ? <ToolView activeTool={activeTool} geography={geography} market={market} onBack={() => setActiveTool(null)} onMarketContext={updateMarketContext} />
          : <HomeView onSelect={selectTool} />}
      </main>
      <SiteFooter onPrivacy={() => setPrivacySignal((value) => value + 1)} />
      <ConsentBanner settingsSignal={privacySignal} />
    </div>
  )
}
