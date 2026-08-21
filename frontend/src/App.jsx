import { useCallback, useEffect, useRef, useState } from 'react'
import DetectionOverlay from './components/DetectionOverlay'
import DetectionList from './components/DetectionList'
import SceneAnalysis from './components/SceneAnalysis'

const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')


const MODES = [
  { id: 'image', label: 'IMAGE', icon: '/logos/image.png', accept: 'image/*' },
  { id: 'video', label: 'VIDEO', icon: '/logos/video.png', accept: 'video/*' },
  { id: 'webcam', label: 'LIVE CAM', icon: '/logos/live.png', accept: null },
]

/** Client-friendly name: "Match Strictness" (was technical "confidence") */
const STRICTNESS = [
  {
    id: 'low',
    label: 'Low',
    value: 0.25,
    tip: 'Shows more results. Good if objects are small or the photo is unclear. May include a few wrong boxes.',
  },
  {
    id: 'medium',
    label: 'Medium',
    value: 0.45,
    tip: 'Balanced — recommended for most photos. Clear objects stay, weak guesses are hidden.',
  },
  {
    id: 'high',
    label: 'High',
    value: 0.7,
    tip: 'Only very clear matches. Cleaner results, but some real objects might be missed.',
  },
]


function MetaBox({ source, res, fps }) {
  return (
    <div className="vl-meta">
      <div>Source: {source || '--'}</div>
      <div>Res: {res || '--'}</div>
      <div>FPS: {fps || '--'}</div>
    </div>
  )
}

export default function App() {
  const [online, setOnline] = useState(false)
  const [latencyMs, setLatencyMs] = useState(null)
  const [mode, setMode] = useState('image')
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [videoResult, setVideoResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [strictness, setStrictness] = useState('medium')
  const conf = STRICTNESS.find((s) => s.id === strictness)?.value ?? 0.45
  const [inferMs, setInferMs] = useState(null)
  const fileRef = useRef(null)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [webcamLive, setWebcamLive] = useState(false)

  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    setWebcamLive(false)
  }, [])

  useEffect(() => {
    let cancelled = false
    async function ping() {
      const t0 = performance.now()
      try {
        // Render free tier can take a long time to wake from sleep
        const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' })
        const ms = Math.round(performance.now() - t0)
        if (!cancelled) {
          setLatencyMs(ms)
          setOnline(res.ok)
        }
      } catch {
        if (!cancelled) {
          setOnline(false)
          setLatencyMs(null)
        }
      }
    }
    ping()
    const id = setInterval(ping, 10000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      stopWebcam()
    }
  }, [stopWebcam])

  const resetResults = () => {
    setResult(null)
    setVideoResult(null)
    setError('')
    setInferMs(null)
  }

  const switchMode = (id) => {
    stopWebcam()
    setMode(id)
    setFile(null)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
    resetResults()
  }

  const onPickFile = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(f)
    setPreviewUrl(URL.createObjectURL(f))
    resetResults()
  }

  const runImagePredict = async (blobOrFile, name = 'frame.jpg') => {
    setLoading(true)
    setError('')
    const t0 = performance.now()
    try {
      const form = new FormData()
      form.append('file', blobOrFile, name)
      const res = await fetch(`${API_BASE}/predict?conf=${conf}&iou=0.45`, {
        method: 'POST',
        body: form,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      setInferMs(Math.round(performance.now() - t0))
      setResult(data)
      setVideoResult(null)
    } catch (err) {
      const msg = err.message || 'Prediction failed'
      setError(
        /fetch|network|failed/i.test(msg)
          ? 'API stopped during detection. On Render Free (512 MB) the model often runs out of memory — upgrade to Standard (2 GB), wait for restart, then try again.'
          : msg,
      )
    } finally {
      setLoading(false)
    }
  }

  const runVideoPredict = async () => {
    if (!file) {
      setError('Choose a video first.')
      return
    }
    setLoading(true)
    setError('')
    const t0 = performance.now()
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`${API_BASE}/predict/video?conf=${conf}&iou=0.45&stride=5&max_frames=60`, {
        method: 'POST',
        body: form,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      setInferMs(Math.round(performance.now() - t0))
      setVideoResult(data)
      setResult(null)
    } catch (err) {
      setError(err.message || 'Video prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const startWebcam = async () => {
    resetResults()
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setWebcamLive(true)
    } catch (err) {
      setError(err.message || 'Webcam access denied')
    }
  }

  const captureWebcamFrame = async () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92))
    setPreviewUrl(canvas.toDataURL('image/jpeg'))
    await runImagePredict(blob, 'webcam.jpg')
  }

  const onRun = async () => {
    if (mode === 'image') {
      if (!file) {
        setError('Upload an image first.')
        return
      }
      await runImagePredict(file, file.name)
    } else if (mode === 'video') {
      await runVideoPredict()
    } else if (mode === 'webcam') {
      if (!webcamLive) await startWebcam()
      else await captureWebcamFrame()
    }
  }

  const sourceLabel =
    mode === 'webcam' ? (webcamLive ? 'webcam' : '--') : file?.name || '--'
  const resLabel = result
    ? `${result.image_width}x${result.image_height}`
    : previewUrl
      ? 'ready'
      : '--'
  const fpsLabel =
    videoResult?.avg_fps != null
      ? videoResult.avg_fps.toFixed(1)
      : inferMs
        ? `${(1000 / Math.max(inferMs, 1)).toFixed(1)}`
        : '--'

  const leftTitle = previewUrl || webcamLive ? 'SOURCE FEED' : 'SOURCE FEED (NO MEDIA)'

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-5 py-6 md:px-8 md:py-8">
      {/* Header */}
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <img src="/logos/brand.png" alt="" className="h-11 w-11 object-contain drop-shadow-[0_0_10px_rgba(0,229,255,0.55)]" />
          <div>
            <h1 className="vl-title text-2xl font-semibold text-white md:text-3xl">VISIONLAB AI</h1>
            <p className="text-sm tracking-wide text-[var(--muted)]">
              Computer Vision Suite - Object Detection v2.1
            </p>
          </div>
        </div>

        <div className="vl-status flex min-w-[240px] items-center justify-between gap-4 px-4 py-3">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <span className={`pulse-dot ${online ? '' : 'off'}`} />
              API Status
            </div>
            <p className="mt-1 text-[11px] tracking-wide text-[var(--muted)]">
              {online ? 'LIVE CONNECTION: FastAPI + YOLOv8' : 'OFFLINE — start backend :8000'}
            </p>
          </div>
          <span className="rounded-full border border-[rgba(34,255,136,0.35)] bg-[rgba(34,255,136,0.08)] px-2.5 py-1 text-xs font-semibold text-[var(--green)]">
            Lat: {latencyMs != null ? `${latencyMs}ms` : '--'}
          </span>
        </div>
      </header>

      {/* Control panel */}
      <section className="vl-panel mb-6 px-5 py-5">
        <div className="mb-5 flex justify-center">
          <div className="vl-mode">
            {MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                className={`vl-mode-btn ${mode === m.id ? 'active' : ''}`}
                onClick={() => switchMode(m.id)}
              >
                <img src={m.icon} alt="" />
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col items-stretch gap-4 md:flex-row md:items-end md:justify-between">
          <div className="min-w-[220px] flex-1 md:max-w-sm">
            <div className="mb-2 flex items-center gap-2 text-sm text-[var(--muted)]">
              <span>Match Strictness</span>
              <span className="vl-info" tabIndex={0} aria-label="What is Match Strictness?">
                i
                <span className="vl-info-tip" role="tooltip">
                  <strong>Match Strictness</strong> controls how picky the detector is.
                  <br />
                  <br />
                  <strong>Low</strong> — show more results (may include unsure guesses).
                  <br />
                  <strong>Medium</strong> — balanced; best for most photos.
                  <br />
                  <strong>High</strong> — only clear, strong matches.
                  <br />
                  <br />
                  It does not retrain the AI — it only hides weak results.
                </span>
              </span>
            </div>
            <div className="vl-level" role="group" aria-label="Match Strictness">
              {STRICTNESS.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  title={s.tip}
                  className={`vl-level-btn ${strictness === s.id ? 'active' : ''}`}
                  onClick={() => setStrictness(s.id)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-end gap-3">
            {mode !== 'webcam' ? (
              <label className="vl-upload">
                UPLOAD MEDIA
                <input
                  ref={fileRef}
                  type="file"
                  accept={MODES.find((m) => m.id === mode)?.accept || '*/*'}
                  className="hidden"
                  onChange={onPickFile}
                />
              </label>
            ) : (
              <button type="button" className="vl-upload" onClick={webcamLive ? stopWebcam : startWebcam}>
                {webcamLive ? 'STOP CAM' : 'START CAM'}
              </button>
            )}

            <button type="button" className="vl-run" disabled={loading} onClick={onRun}>
              <span className="vl-play" />
              {loading ? 'RUNNING…' : mode === 'webcam' && webcamLive ? 'CAPTURE & RUN' : 'RUN INFERENCE'}
            </button>
          </div>
        </div>

        {error && (
          <p className="mt-4 rounded-lg border border-rose-500/40 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">
            {error}
          </p>
        )}
      </section>

      {/* Dual panels */}
      <div className="grid gap-5 lg:grid-cols-2">
        <section className="vl-panel relative min-h-[300px] overflow-hidden p-4">
          <div className="mb-3 flex items-start justify-between gap-3">
            <h2 className="text-sm font-semibold tracking-wide text-[var(--muted)]">{leftTitle}</h2>
            <MetaBox source={sourceLabel} res={resLabel} fps={fpsLabel} />
          </div>

          <div className="flex min-h-[220px] items-center justify-center">
            {mode === 'webcam' && webcamLive && !result && (
              <video ref={videoRef} className="max-h-[260px] w-full rounded-lg object-contain" muted playsInline />
            )}
            {mode === 'video' && previewUrl && !result && (
              <video src={previewUrl} controls className="max-h-[260px] w-full rounded-lg object-contain" />
            )}
            {previewUrl && result ? (
              <DetectionOverlay
                imageUrl={previewUrl}
                detections={result.detections}
                imageWidth={result.image_width}
                imageHeight={result.image_height}
              />
            ) : previewUrl && mode === 'image' ? (
              <img src={previewUrl} alt="source" className="max-h-[260px] w-full rounded-lg object-contain" />
            ) : !webcamLive && !previewUrl ? (
              <div className="flex flex-col items-center gap-2 text-center">
                <img src="/logos/files.png" alt="" className="vl-empty-icon" />
                <p className="text-[11px] tracking-[0.16em] text-[var(--muted)]">DROP FILE OR SELECT MODE ABOVE</p>
              </div>
            ) : null}
          </div>
          <canvas ref={canvasRef} className="hidden" />
        </section>

        <section className="vl-panel relative min-h-[300px] overflow-hidden p-4">
          <div className="mb-3 flex items-start justify-between gap-3">
            <h2 className="text-sm font-semibold tracking-wide text-[var(--muted)]">LIVE INFERENCE (RESULTS)</h2>
            <MetaBox
              source={result || videoResult ? 'yolov8n' : '--'}
              res={result ? `${result.detections?.length || 0} det` : videoResult ? `${videoResult.frames_processed} frm` : '--'}
              fps={inferMs != null ? `${inferMs}ms` : '--'}
            />
          </div>

          {result || videoResult ? (
            <div className="vl-scroll max-h-[260px] overflow-auto pr-1">
              {result?.analysis && <SceneAnalysis analysis={result.analysis} />}
              {result && <DetectionList detections={result.detections} model={result.model} />}
              {videoResult && (
                <div className="space-y-2 text-sm text-slate-300">
                  <p>
                    Frames: {videoResult.frames_processed} · Avg FPS: {videoResult.avg_fps?.toFixed?.(2)} · Latency:{' '}
                    {videoResult.avg_latency_ms?.toFixed?.(0)} ms
                  </p>
                  <ul className="space-y-2">
                    {videoResult.frame_summaries?.slice(0, 24).map((f) => (
                      <li key={f.frame_index} className="rounded-md border border-cyan-900/40 bg-slate-950/50 px-3 py-2">
                        Frame {f.frame_index}: {f.num_detections} objects
                        {f.top_classes?.length ? ` — ${f.top_classes.join(', ')}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="flex min-h-[220px] flex-col items-center justify-center gap-2 text-center">
              <img src="/logos/brand.png" alt="" className="vl-empty-icon" />
              <p className="text-[11px] tracking-[0.16em] text-[var(--muted)]">VISUALIZATIONS WILL APPEAR HERE</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
