import {
  Activity,
  Calculator,
  Map,
  MessageSquareText,
  Scale,
  type LucideIcon,
} from 'lucide-react'

import type { ToolId } from '../types'

export interface ToolDefinition {
  id: ToolId
  title: string
  description: string
  action: string
  tone: 'blue' | 'green' | 'amber' | 'violet'
  icon: LucideIcon
}

export const TOOLS: ToolDefinition[] = [
  {
    id: 'observatory',
    title: 'Seguir el mercado estatal',
    description: 'Precios, hipotecas, Euríbor y TAE con evolución, fuente y periodo.',
    action: 'Abrir observatorio',
    icon: Activity,
    tone: 'blue',
  },
  {
    id: 'market',
    title: 'Entender una zona',
    description: 'Precio, renta, esfuerzo y financiación con fuente y fecha visibles.',
    action: 'Explorar el mapa',
    icon: Map,
    tone: 'blue',
  },
  {
    id: 'budget',
    title: 'Saber cuánto puedo comprar',
    description: 'Un rango sostenible según ingresos, ahorro, deudas y colchón.',
    action: 'Calcular mi rango',
    icon: Calculator,
    tone: 'green',
  },
  {
    id: 'mortgage',
    title: 'Comparar ofertas',
    description: 'Fija, variable o mixta: cuota, TAE, comisiones y vinculaciones.',
    action: 'Comparar hipotecas',
    icon: Scale,
    tone: 'amber',
  },
  {
    id: 'questions',
    title: 'Preparar mi negociación',
    description: 'Convierte tu caso en preguntas concretas y ayúdanos a cubrir dudas reales.',
    action: 'Plantear mi caso',
    icon: MessageSquareText,
    tone: 'violet',
  },
]

export function toolById(id: ToolId) {
  return TOOLS.find((tool) => tool.id === id)!
}
