import { Loader2 } from 'lucide-react'

interface Props {
  className?: string
}

export default function Spinner({ className = '' }: Props) {
  return <Loader2 className={`animate-spin ${className}`} />
}
