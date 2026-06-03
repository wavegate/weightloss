import { TeamHQScene } from './TeamHQScene'

export function CoachTeamStage() {
  return (
    <section
      aria-label="Your coaching team"
      className="relative h-full min-h-0 w-full bg-slate-950"
    >
      <p className="pointer-events-none absolute left-4 top-4 z-10 text-xs font-medium text-slate-500">
        Drag to orbit · right-drag or two-finger drag to pan · click a teammate to talk
      </p>
      <TeamHQScene layout="room" />
    </section>
  )
}
