import { useState, useEffect } from 'react';
import { getPatientNotes, createNote, updateNote, deleteNote, type Note } from '../../services/notesApi';
import { getUser } from '../../utils/auth';
import './ProviderNotes.css';

interface ProviderNotesProps {
  patientId: string;
}

export function ProviderNotes({ patientId }: ProviderNotesProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newNoteContent, setNewNoteContent] = useState('');
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const user = getUser();
  const isProvider = user?.role === 'provider';

  useEffect(() => {
    loadNotes();
  }, [patientId]);

  const loadNotes = async () => {
    setLoading(true);
    setError(null);
    try {
      // Check if user is authenticated
      if (!user) {
        setError('You must be logged in to view notes. Please log in and try again.');
        setLoading(false);
        return;
      }
      
      const response = await getPatientNotes(patientId);
      if (response.status === 'success') {
        setNotes(response.data.notes);
      } else {
        console.error('Failed to load notes:', response.error);
        if (response.error?.toLowerCase().includes('unauthorized') || response.error?.toLowerCase().includes('401')) {
          setError('Authentication failed. Please log out and log back in.');
        } else {
          setError(response.error || 'Failed to load notes');
        }
      }
    } catch (err) {
      console.error('Error loading notes:', err);
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNote = async () => {
    if (!newNoteContent.trim()) {
      setError('Note content cannot be empty');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const response = await createNote(patientId, newNoteContent.trim());
      if (response.status === 'success') {
        setNewNoteContent('');
        await loadNotes();
      } else {
        console.error('Failed to create note:', response.error);
        // Check if it's an authentication error
        if (response.error?.toLowerCase().includes('unauthorized') || response.error?.toLowerCase().includes('401')) {
          setError('Authentication failed. Please make sure you are logged in as a provider.');
        } else if (response.error?.toLowerCase().includes('403') || response.error?.toLowerCase().includes('forbidden')) {
          setError('Only providers can create notes. Please log in as a provider.');
        } else {
          setError(response.error || 'Failed to create note');
        }
      }
    } catch (err) {
      console.error('Error creating note:', err);
      setError(err instanceof Error ? err.message : 'Failed to create note');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartEdit = (note: Note) => {
    setEditingNoteId(note.id);
    setEditingContent(note.content);
  };

  const handleCancelEdit = () => {
    setEditingNoteId(null);
    setEditingContent('');
  };

  const handleUpdateNote = async (noteId: string) => {
    if (!editingContent.trim()) {
      setError('Note content cannot be empty');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const response = await updateNote(patientId, noteId, editingContent.trim());
      if (response.status === 'success') {
        setEditingNoteId(null);
        setEditingContent('');
        await loadNotes();
      } else {
        setError(response.error || 'Failed to update note');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update note');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    if (!confirm('Are you sure you want to delete this note?')) {
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const response = await deleteNote(patientId, noteId);
      if (response.status === 'success') {
        await loadNotes();
      } else {
        setError(response.error || 'Failed to delete note');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete note');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="provider-notes">
      <div className="provider-notes-header">
        <h3>Provider Notes</h3>
        <p className="notes-description">
          Add notes and reminders about this patient. Notes are visible to both you and the patient.
        </p>
      </div>

      {error && (
        <div className="notes-error">
          <span>⚠️</span>
          <span>{error}</span>
          <button onClick={() => setError(null)} className="error-dismiss">×</button>
        </div>
      )}

      {isProvider ? (
        <div className="notes-form">
          <textarea
            className="notes-textarea"
            placeholder="Enter a note about this patient..."
            value={newNoteContent}
            onChange={(e) => setNewNoteContent(e.target.value)}
            rows={4}
            disabled={isSubmitting}
          />
          <button
            className="notes-submit-button"
            onClick={handleCreateNote}
            disabled={isSubmitting || !newNoteContent.trim()}
          >
            {isSubmitting ? 'Adding...' : 'Add Note'}
          </button>
        </div>
      ) : (
        <div className="notes-info">
          <p>You must be logged in as a provider to add notes.</p>
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
          <p>No notes yet. Add your first note above.</p>
        </div>
      ) : (
        <div className="notes-list">
          {notes.map((note) => (
            <div key={note.id} className="note-item">
              {editingNoteId === note.id ? (
                <div className="note-edit">
                  <textarea
                    className="notes-textarea"
                    value={editingContent}
                    onChange={(e) => setEditingContent(e.target.value)}
                    rows={4}
                    disabled={isSubmitting}
                  />
                  <div className="note-edit-actions">
                    <button
                      className="notes-save-button"
                      onClick={() => handleUpdateNote(note.id)}
                      disabled={isSubmitting || !editingContent.trim()}
                    >
                      {isSubmitting ? 'Saving...' : 'Save'}
                    </button>
                    <button
                      className="notes-cancel-button"
                      onClick={handleCancelEdit}
                      disabled={isSubmitting}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="note-content">{note.content}</div>
                  <div className="note-meta">
                    <span className="note-date">
                      {formatDate(note.updated_at)}
                      {note.updated_at !== note.created_at && ' (edited)'}
                    </span>
                    {isProvider && (
                      <div className="note-actions">
                        <button
                          className="note-action-button"
                          onClick={() => handleStartEdit(note)}
                          disabled={isSubmitting}
                        >
                          Edit
                        </button>
                        <button
                          className="note-action-button delete"
                          onClick={() => handleDeleteNote(note.id)}
                          disabled={isSubmitting}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

