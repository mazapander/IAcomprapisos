import { useCallback, useEffect, useState } from 'react'

import { getMarketSummary } from '../api'
import { FALLBACK_GEOGRAPHIES } from '../data/geographies'
import type { Geography, MarketSummary } from '../types'

const DEFAULT_GEOGRAPHY = FALLBACK_GEOGRAPHIES.find((item) => item.code === 'PROV:24')!

export function useBuyerMarketContext() {
  const [geography, setGeography] = useState<Geography>(DEFAULT_GEOGRAPHY)
  const [market, setMarket] = useState<MarketSummary | null>(null)

  useEffect(() => {
    getMarketSummary(DEFAULT_GEOGRAPHY.code, { homeSize: 90, ltv: 80, term: 25 })
      .then(setMarket)
      .catch(() => setMarket(null))
  }, [])

  const updateMarketContext = useCallback(
    (context: { geography: Geography; summary: MarketSummary | null }) => {
      setGeography(context.geography)
      setMarket(context.summary)
    },
    [],
  )

  return { geography, market, updateMarketContext }
}
