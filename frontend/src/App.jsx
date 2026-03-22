import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function App() {
  const [languages, setLanguages] = useState({})
  const [loadingLang, setLoadingLang] = useState(true)
  const [tab, setTab] = useState('text')

  const [textInput, setTextInput] = useState('')
  const [fromLang, setFromLang] = useState('auto')
  const [toLang, setToLang] = useState('en')
  const [translatedText, setTranslatedText] = useState('')
  const [textError, setTextError] = useState('')
  const [translatingText, setTranslatingText] = useState(false)

  const [file, setFile] = useState(null)
  const [fileFrom, setFileFrom] = useState('auto')
  const [fileTo, setFileTo] = useState('en')
  const [fileError, setFileError] = useState('')
  const [translatingFile, setTranslatingFile] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/api/languages`)
      .then((r) => r.json())
      .then((data) => setLanguages(data.languages || {}))
      .catch(() => setLanguages({ en: 'English' }))
      .finally(() => setLoadingLang(false))
  }, [])

  const languageOptions = [{ code: 'auto', name: 'Auto-detect' }, ...Object.entries(languages).map(([code, name]) => ({ code, name }))]

  const handleTranslateText = async () => {
    if (!textInput.trim()) {
      setTextError('Type text before translating.')
      return
    }
    setTranslatingText(true)
    setTextError('')
    try {
      const form = new URLSearchParams()
      form.append('text', textInput)
      form.append('source', fromLang)
      form.append('target', toLang)

      const res = await fetch(`${API_BASE}/api/translate-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => null)
        throw new Error(err?.detail || 'Translation failed')
      }
      const payload = await res.json()
      setTranslatedText(payload.translated || '')
    } catch (e) {
      setTextError(e.message)
    } finally {
      setTranslatingText(false)
    }
  }

  const handleTranslateFile = async () => {
    if (!file) {
      setFileError('Select a PDF, DOCX, or XLSX file first.')
      return
    }
    setFileError('')
    setTranslatingFile(true)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('source', fileFrom)
      form.append('target', fileTo)

      const res = await fetch(`${API_BASE}/api/translate-document`, {
        method: 'POST',
        body: form,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => null)
        throw new Error(err?.detail || 'Document translation failed')
      }
      const blob = await res.blob()
      const contentDisposition = res.headers.get('Content-Disposition')
      let filename = 'translated_document'
      if (contentDisposition) {
        const m = /filename="?([^\";]+)"?/.exec(contentDisposition)
        if (m) filename = m[1]
      }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setFileError(e.message)
    } finally {
      setTranslatingFile(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="header">
        <div>
          <p className="eyebrow">Sabio Translator</p>
          <h1>React + OpenAI translation app</h1>
          <p className="subtitle">Translate text or upload files (PDF/DOCX/XLSX).</p>
        </div>
        <div className="pill">Backend: FastAPI • OpenAI • React UI</div>
      </header>

      <section className="tabs">
        <button className={tab === 'text' ? 'active' : ''} onClick={() => setTab('text')}>Quick Text</button>
        <button className={tab === 'file' ? 'active' : ''} onClick={() => setTab('file')}>Document</button>
      </section>

      {tab === 'text' ? (
        <section className="card">
          <h2>Quick text translation</h2>
          <textarea value={textInput} onChange={(e) => setTextInput(e.target.value)} placeholder="Enter text to translate..." rows={8} />

          <div className="row">
            <div className="field"><label>From</label>
              <select value={fromLang} onChange={(e) => setFromLang(e.target.value)}>
                {languageOptions.map((l) => <option key={l.code} value={l.code}>{l.name} {l.code === 'auto' ? '' : `(${l.code})`}</option>)}
              </select>
            </div>
            <div className="field"><label>To</label>
              <select value={toLang} onChange={(e) => setToLang(e.target.value)}>
                {Object.entries(languages).map(([code, name]) => <option key={code} value={code}>{name} ({code})</option>)}
              </select>
            </div>
          </div>

          <button onClick={handleTranslateText} disabled={translatingText}>{translatingText ? 'Translating...' : 'Translate Text'}</button>
          {textError && <div className="error">{textError}</div>}
          {translatedText && <textarea readOnly value={translatedText} rows={8} />}
        </section>
      ) : (
        <section className="card">
          <h2>Document translation</h2>
          <input type="file" accept=".pdf,.docx,.xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <div className="row">
            <div className="field"><label>From</label>
              <select value={fileFrom} onChange={(e) => setFileFrom(e.target.value)}>
                <option value="auto">Auto-detect</option>
                {Object.entries(languages).map(([code, name]) => <option key={code} value={code}>{name} ({code})</option>)}
              </select>
            </div>
            <div className="field"><label>To</label>
              <select value={fileTo} onChange={(e) => setFileTo(e.target.value)}>
                {Object.entries(languages).map(([code, name]) => <option key={code} value={code}>{name} ({code})</option>)}
              </select>
            </div>
          </div>
          <button onClick={handleTranslateFile} disabled={translatingFile}>{translatingFile ? 'Translating...' : 'Translate & Download'}</button>
          {fileError && <div className="error">{fileError}</div>}
        </section>
      )}

      <footer className="footer">Make sure OPENAI_API_KEY is set in your environment when running backend.</footer>
    </div>
  )
}

export default App
