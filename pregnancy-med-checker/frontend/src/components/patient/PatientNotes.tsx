import { useState, useEffect } from 'react';
import { getPatientNotes, type Note } from '../../services/notesApi';
import './PatientNotes.css';

interface PatientNotesProps {
  patientId: string;
}

export function PatientNotes({ patientId }: PatientNotesProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNotes();
  }, [patientId]);

  const loadNotes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getPatientNotes(patientId);
      if (response.status === 'success') {
        setNotes(response.data.notes);
      } else {
        setError(response.error || 'Failed to load notes');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="patient-notes">
      <div className="patient-notes-header">
        <h3>Provider Notes</h3>
        <p className="notes-description">
          Notes from your healthcare provider about your care and health.
        </p>
      </div>

      {error && (
        <div className="notes-error">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="notes-loading">
          <div className="loading-spinner" />
          <p>Loading notes...</p>
        </div>
      ) : notes.length === 0 ? (
        <div className="notes-empty">
          <div className="empty-icon">📝</div>
          <p>No notes from your provider yet.</p>
        </div>
      ) : (
        <div className="notes-list">
          {notes.map((note) => (
            <div key={note.id} className="note-item">
              <div className="note-content">{note.content}</div>
              <div className="note-meta">
                <span className="note-date">
                  {formatDate(note.updated_at)}
                  {note.updated_at !== note.created_at && ' (updated)'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

