import { useState } from 'react'
import { motion } from 'framer-motion'
import { useSuspects } from '@/hooks/useSuspects'
import { RelationshipGraph } from '@/components/suspects/RelationshipGraph'
import { SuspectCard } from '@/components/suspects/SuspectCard'
import { useCaseStore } from '@/store/caseStore'

export function SuspectBoardPage() {
  const caseId = useCaseStore((s) => s.caseId)
  const { data, isLoading, error } = useSuspects()
  const [selectedSuspect, setSelectedSuspect] = useState<string | null>(null)

  if (!caseId) {
    return (
      <div
        className="flex items-center justify-center h-full"
        style={{ color: 'var(--text-muted)' }}
      >
        <div className="text-center">
          <div className="font-stamp text-xs tracking-widest mb-2" style={{ fontSize: '0.65rem' }}>
            NO ACTIVE CASE
          </div>
          <div className="font-reading text-sm" style={{ color: 'var(--text-muted)' }}>
            Open or upload a case file to view suspects.
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div
          className="font-stamp text-xs tracking-widest animate-pulse"
          style={{ color: 'var(--accent-amber)', fontSize: '0.65rem' }}
        >
          LOADING PERSONS OF INTEREST...
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="font-stamp text-xs tracking-widest" style={{ color: 'var(--signal-red)', fontSize: '0.65rem' }}>
          FAILED TO LOAD SUSPECT DATA
        </div>
      </div>
    )
  }

  const sortedSuspects = [...data.suspects].sort((a, b) => b.total_score - a.total_score)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex h-full overflow-hidden"
    >
      {/* Left: Relationship Graph — corkboard surface */}
      <div
        className="flex-1 relative overflow-hidden"
        style={{ backgroundColor: 'var(--bg-corkboard)' }}
      >
        {/* Section header */}
        <div
          className="absolute top-0 left-0 right-0 z-10 px-6 py-3 flex items-center justify-between"
          style={{
            borderBottom: '1px solid rgba(46,47,54,0.6)',
            backgroundColor: 'rgba(43, 33, 24, 0.85)',
          }}
        >
          <div className="font-report text-sm tracking-widest uppercase" style={{ color: 'var(--text-primary)' }}>
            Persons of Interest
          </div>
          <div className="font-stamp text-xs" style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}>
            {data.suspects.length} SUSPECTS — {data.edges.length} CONNECTIONS
          </div>
        </div>

        <div className="absolute inset-0 pt-12">
          <RelationshipGraph
            suspects={data.suspects}
            edges={data.edges}
            onSelectSuspect={setSelectedSuspect}
          />
        </div>
      </div>

      {/* Right: Suspect Card Panel */}
      <div
        className="flex flex-col overflow-y-auto"
        style={{
          width: '280px',
          minWidth: '280px',
          borderLeft: '1px solid var(--divider)',
          backgroundColor: 'var(--bg-charcoal)',
        }}
      >
        {/* Panel header */}
        <div
          className="px-4 py-3 flex-shrink-0"
          style={{ borderBottom: '1px solid var(--divider)' }}
        >
          <div className="font-stamp text-xs tracking-widest" style={{ color: 'var(--accent-brass)', fontSize: '0.6rem' }}>
            CASE DOSSIERS
          </div>
        </div>

        {/* Suspect cards list */}
        <div className="flex-1 p-3 space-y-2 overflow-y-auto">
          {sortedSuspects.map((suspect, index) => (
            <SuspectCard
              key={suspect.name}
              suspect={suspect}
              index={index}
              rank={index + 1}
              isSelected={selectedSuspect === suspect.name}
              onClick={() =>
                setSelectedSuspect(
                  selectedSuspect === suspect.name ? null : suspect.name
                )
              }
            />
          ))}

          {sortedSuspects.length === 0 && (
            <div
              className="font-stamp text-xs text-center py-8"
              style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}
            >
              NO SUSPECTS IDENTIFIED
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
