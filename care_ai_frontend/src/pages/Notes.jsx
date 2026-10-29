import React, { useState, useEffect, useRef } from 'react';
import { uploadVoiceNote, uploadVideoNote, submitTextNote, listNotes, generateHandover } from '../services/api';
import { Mic, MicOff, Video, FileText, Upload, Clock, AlertTriangle, CheckCircle } from 'lucide-react';

export default function Notes() {
  const [tab, setTab] = useState('record');    // record | upload | text | history | handover
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // Recording state
  const [recording, setRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaType, setMediaType] = useState('audio'); // audio | video
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  // Text note
  const [textNote, setTextNote] = useState('');
  const [clientName, setClientName] = useState('');

  // Handover
  const [handover, setHandover] = useState(null);

  useEffect(() => {
    if (tab === 'history') {
      listNotes(50, 0).then(d => setNotes(d.notes)).catch(() => {});
    }
  }, [tab]);

  // --- Recording ---
  const startRecording = async () => {
    setError('');
    setResult(null);
    chunksRef.current = [];

    try {
      const constraints = mediaType === 'video'
        ? { audio: true, video: true }
        : { audio: true };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      const mimeType = mediaType === 'video' ? 'video/webm' : 'audio/webm';
      const recorder = new MediaRecorder(stream, { mimeType });

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
      };

      mediaRecorderRef.current = recorder;
      recorder.start(1000); // Collect data every second
      setRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (err) {
      setError('Could not access microphone. Please allow microphone access in your browser settings.');
    }
  };

  const stopRecording = async () => {
    if (!mediaRecorderRef.current) return;

    setRecording(false);
    clearInterval(timerRef.current);

    return new Promise((resolve) => {
      mediaRecorderRef.current.onstop = async () => {
        mediaRecorderRef.current.stream?.getTracks().forEach(t => t.stop());

        const ext = mediaType === 'video' ? 'webm' : 'webm';
        const blob = new Blob(chunksRef.current, { type: `${mediaType}/webm` });
        const file = new File([blob], `recording.${ext}`, { type: `${mediaType}/webm` });

        setLoading(true);
        try {
          const uploadFn = mediaType === 'video' ? uploadVideoNote : uploadVoiceNote;
          const res = await uploadFn(file, clientName);
          setResult(res);
        } catch (err) {
          setError(err.message || 'Upload failed');
        } finally {
          setLoading(false);
        }

        resolve();
      };

      mediaRecorderRef.current.stop();
    });
  };

  // --- File upload ---
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError('');
    setResult(null);
    setLoading(true);

    try {
      const isVideo = file.type.startsWith('video/');
      const uploadFn = isVideo ? uploadVideoNote : uploadVoiceNote;
      const res = await uploadFn(file, clientName);
      setResult(res);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  // --- Text note ---
  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!textNote.trim()) return;
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const res = await submitTextNote(textNote, clientName);
      setResult(res);
      setTextNote('');
    } catch (err) {
      setError(err.message || 'Submit failed');
    } finally {
      setLoading(false);
    }
  };

  // --- Handover ---
  const handleHandover = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await generateHandover(12);
      setHandover(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <main className="main-content">
      <div className="container" style={{ maxWidth: 900 }}>
        <h2 style={{ marginBottom: 'var(--space-lg)' }}>Clinical Notes</h2>

        {/* Tabs */}
        <div className="tabs">
          <button className={`tab ${tab === 'record' ? 'active' : ''}`} onClick={() => setTab('record')}>
            <Mic size={16} style={{ marginRight: 6 }} /> Record
          </button>
          <button className={`tab ${tab === 'upload' ? 'active' : ''}`} onClick={() => setTab('upload')}>
            <Upload size={16} style={{ marginRight: 6 }} /> Upload
          </button>
          <button className={`tab ${tab === 'text' ? 'active' : ''}`} onClick={() => setTab('text')}>
            <FileText size={16} style={{ marginRight: 6 }} /> Text
          </button>
          <button className={`tab ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>
            <Clock size={16} style={{ marginRight: 6 }} /> History
          </button>
          <button className={`tab ${tab === 'handover' ? 'active' : ''}`} onClick={() => setTab('handover')}>
            Handover
          </button>
        </div>

        {/* Client name field (shared) */}
        {(tab === 'record' || tab === 'upload' || tab === 'text') && (
          <div className="form-group" style={{ maxWidth: 300 }}>
            <label className="form-label">Client name (optional)</label>
            <input type="text" className="form-input" value={clientName} onChange={(e) => setClientName(e.target.value)} placeholder="e.g. Mrs Johnson" />
          </div>
        )}

        {error && <div className="alert alert-danger">{error}</div>}

        {/* Record tab */}
        {tab === 'record' && (
          <div>
            {/* Audio/Video toggle */}
            <div style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-lg)' }}>
              <button className={`btn ${mediaType === 'audio' ? 'btn-secondary' : 'btn-outline'} btn-sm`} onClick={() => setMediaType('audio')}>
                <Mic size={14} /> Audio only
              </button>
              <button className={`btn ${mediaType === 'video' ? 'btn-secondary' : 'btn-outline'} btn-sm`} onClick={() => setMediaType('video')}>
                <Video size={14} /> Video
              </button>
            </div>

            <div className={`recorder-wrapper ${recording ? 'recording' : ''}`}>
              {recording ? (
                <>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--nhs-red)', fontVariantNumeric: 'tabular-nums' }}>
                    {formatTime(recordingTime)}
                  </div>
                  <p style={{ color: 'var(--nhs-mid-grey)' }}>Recording {mediaType}...</p>
                  <button className="record-btn recording" onClick={stopRecording}>
                    <MicOff size={28} />
                  </button>
                  <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)' }}>Tap to stop and process</p>
                </>
              ) : (
                <>
                  <button className="record-btn" onClick={startRecording} disabled={loading}>
                    {loading ? <div className="spinner" /> : <Mic size={28} />}
                  </button>
                  <p style={{ color: 'var(--nhs-dark-grey)', fontWeight: 500 }}>
                    {loading ? 'Processing...' : `Tap to start ${mediaType} recording`}
                  </p>
                </>
              )}
            </div>
          </div>
        )}

        {/* Upload tab */}
        {tab === 'upload' && (
          <div className="recorder-wrapper">
            <Upload size={40} color="var(--nhs-mid-grey)" />
            <p style={{ color: 'var(--nhs-dark-grey)', fontWeight: 500 }}>
              Upload an audio or video file
            </p>
            <p style={{ color: 'var(--nhs-mid-grey)', fontSize: '0.85rem' }}>
              Supported: MP3, WAV, M4A, OGG, MP4, MOV, AVI, WebM
            </p>
            <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
              {loading ? <><div className="spinner" /> Processing...</> : 'Choose file'}
              <input type="file" accept="audio/*,video/*" onChange={handleFileUpload} style={{ display: 'none' }} disabled={loading} />
            </label>
          </div>
        )}

        {/* Text tab */}
        {tab === 'text' && (
          <form onSubmit={handleTextSubmit}>
            <div className="form-group">
              <label className="form-label">Type or paste your clinical note</label>
              <textarea
                className="form-textarea"
                value={textNote}
                onChange={(e) => setTextNote(e.target.value)}
                placeholder="e.g. Visited Mrs Johnson at 2pm. She complained of pain in her left knee. Administered paracetamol 500mg as per care plan. Mood was low today, mentioned feeling lonely. Encouraged her to attend the day centre tomorrow."
                style={{ minHeight: 200 }}
                disabled={loading}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading || !textNote.trim()}>
              {loading ? <><div className="spinner" /> Processing...</> : 'Generate clinical note'}
            </button>
          </form>
        )}

        {/* Result */}
        {result && (
          <div className="card" style={{ marginTop: 'var(--space-xl)', borderLeft: '4px solid var(--nhs-green)' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-md)' }}>
              <CheckCircle size={20} color="var(--nhs-green)" /> Clinical Note Generated
            </h3>

            {/* Transcript */}
            {result.transcript && (
              <div style={{ marginBottom: 'var(--space-lg)' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xs)' }}>Transcript</h4>
                <p style={{ background: 'var(--nhs-pale-grey)', padding: 'var(--space-md)', borderRadius: 'var(--radius-sm)', fontSize: '0.9rem' }}>
                  {result.transcript}
                </p>
              </div>
            )}

            {/* Summary */}
            {result.clinical_note?.summary && (
              <div style={{ marginBottom: 'var(--space-lg)' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xs)' }}>AI Summary</h4>
                <p style={{ lineHeight: 1.6 }}>{result.clinical_note.summary}</p>
              </div>
            )}

            {/* Actions */}
            {result.clinical_note?.actions?.length > 0 && (
              <div style={{ marginBottom: 'var(--space-lg)' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-sm)' }}>Actions</h4>
                {result.clinical_note.actions.map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'start', gap: 'var(--space-sm)', padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--nhs-pale-grey)' }}>
                    <span className={`badge badge-${a.priority === 'urgent' ? 'urgent' : a.priority === 'routine' ? 'routine' : 'neutral'}`}>
                      {a.priority}
                    </span>
                    <div>
                      <p style={{ fontWeight: 500 }}>{a.action}</p>
                      {a.time && <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)' }}>Time: {a.time}</p>}
                      {a.medication && <p style={{ fontSize: '0.85rem', color: 'var(--nhs-blue)' }}>💊 {a.medication}</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Concerns */}
            {result.clinical_note?.concerns?.length > 0 && (
              <div className="alert alert-warning">
                <h4 style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-sm)' }}>
                  <AlertTriangle size={16} /> Concerns Flagged
                </h4>
                <ul style={{ paddingLeft: 'var(--space-lg)', margin: 0 }}>
                  {result.clinical_note.concerns.map((c, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>{c}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.duration_seconds && (
              <p style={{ fontSize: '0.8rem', color: 'var(--nhs-mid-grey)', marginTop: 'var(--space-md)' }}>
                Recording duration: {Math.round(result.duration_seconds)}s
              </p>
            )}

            {result.media_destroyed && (
              <div style={{ 
                display: 'flex', alignItems: 'center', gap: 'var(--space-sm)',
                marginTop: 'var(--space-md)', padding: 'var(--space-sm) var(--space-md)',
                background: '#e8f5e9', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem',
                color: 'var(--nhs-green)'
              }}>
                🔒 Recording securely destroyed — only text has been retained
              </div>
            )}
          </div>
        )}

        {/* History tab */}
        {tab === 'history' && (
          <div className="notes-grid">
            {notes.length === 0 ? (
              <p style={{ color: 'var(--nhs-mid-grey)', textAlign: 'center', padding: 'var(--space-xxl)' }}>
                No notes yet.
              </p>
            ) : notes.map(note => (
              <div key={note.id} className="note-card">
                <div className="note-card-header">
                  <span className="note-card-type">
                    {note.input_type === 'audio' && <Mic size={14} />}
                    {note.input_type === 'video' && <Video size={14} />}
                    {note.input_type === 'text' && <FileText size={14} />}
                    {' '}{note.input_type}
                    {note.duration_seconds && ` · ${Math.round(note.duration_seconds)}s`}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--nhs-mid-grey)' }}>
                    {new Date(note.created_at).toLocaleString('en-GB')}
                  </span>
                </div>
                <p className="note-card-summary">
                  {note.clinical_note?.summary || note.transcript?.slice(0, 200) || 'No content'}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Handover tab */}
        {tab === 'handover' && (
          <div>
            <p style={{ color: 'var(--nhs-dark-grey)', marginBottom: 'var(--space-lg)' }}>
              Generate a shift handover note from all your clinical notes in the past 12 hours. 
              Summarises key events, outstanding actions, and concerns for the next carer.
            </p>
            <button className="btn btn-primary" onClick={handleHandover} disabled={loading}>
              {loading ? <><div className="spinner" /> Generating...</> : 'Generate shift handover'}
            </button>

            {handover && (
              <div className="card" style={{ marginTop: 'var(--space-xl)', borderLeft: '4px solid var(--nhs-blue)' }}>
                <h3 style={{ marginBottom: 'var(--space-md)' }}>Shift Handover Note</h3>
                {handover.success ? (
                  <>
                    <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{handover.handover_note}</p>
                    <p style={{ fontSize: '0.8rem', color: 'var(--nhs-mid-grey)', marginTop: 'var(--space-md)' }}>
                      Based on {handover.notes_summarised} note(s)
                    </p>
                  </>
                ) : (
                  <p style={{ color: 'var(--nhs-mid-grey)' }}>{handover.error || 'No notes found for handover'}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
