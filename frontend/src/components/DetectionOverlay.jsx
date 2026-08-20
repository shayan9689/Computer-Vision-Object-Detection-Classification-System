import { useEffect, useRef } from 'react'

const COLORS = ['#38bdf8', '#a78bfa', '#34d399', '#fbbf24', '#f472b6', '#fb7185']

export default function DetectionOverlay({ imageUrl, detections, imageWidth, imageHeight }) {
  const canvasRef = useRef(null)
  const imgRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const img = imgRef.current
    if (!canvas || !img || !imageUrl) return

    const draw = () => {
      const displayW = img.clientWidth
      const displayH = img.clientHeight
      canvas.width = displayW
      canvas.height = displayH
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, displayW, displayH)
      ctx.drawImage(img, 0, 0, displayW, displayH)

      const sx = displayW / imageWidth
      const sy = displayH / imageHeight

      detections.forEach((det, i) => {
        const { x1, y1, x2, y2 } = det.bbox
        const color = COLORS[i % COLORS.length]
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.strokeRect(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
        const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`
        ctx.font = '12px Segoe UI, sans-serif'
        const tw = ctx.measureText(label).width + 8
        ctx.fillStyle = color
        ctx.fillRect(x1 * sx, Math.max(0, y1 * sy - 18), tw, 18)
        ctx.fillStyle = '#0f172a'
        ctx.fillText(label, x1 * sx + 4, Math.max(12, y1 * sy - 5))
      })
    }

    if (img.complete) draw()
    else img.onload = draw
    window.addEventListener('resize', draw)
    return () => window.removeEventListener('resize', draw)
  }, [imageUrl, detections, imageWidth, imageHeight])

  return (
    <div className="relative w-full">
      <img ref={imgRef} src={imageUrl} alt="source" className="max-h-[260px] w-full object-contain opacity-0 absolute" />
      <canvas ref={canvasRef} className="max-h-[260px] w-full rounded-lg" />
    </div>
  )
}
