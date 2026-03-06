import { useState, useEffect } from 'react';
import './MedicationReminders.css';

interface Medication {
  id?: string;
  medication?: {
    display?: string;
    reference?: string;
  };
  medicationCodeableConcept?: {
    text?: string;
    coding?: Array<{
      display?: string;
      code?: string;
    }>;
  };
  dosageInstruction?: Array<{
    text?: string;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

interface MedicationRemindersProps {
  medications: Medication[];
}

interface MedicationReminder {
  medicationId: string;
  medicationName: string;
  times: string[]; // Array of time strings in HH:mm format
  enabled: boolean;
}

const STORAGE_KEY = 'medication_reminders';

export function MedicationReminders({ medications }: MedicationRemindersProps) {
  const [reminders, setReminders] = useState<Map<string, MedicationReminder>>(new Map());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [upcomingReminders, setUpcomingReminders] = useState<Array<{
    medicationName: string;
    time: string;
    minutesUntil: number;
  }>>([]);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  const [notifiedTimes, setNotifiedTimes] = useState<Set<string>>(new Set());

  const extractMedicationName = (med: Medication): string => {
    if (typeof med.medication === 'string' && med.medication) {
      return med.medication;
    }
    if ((med as any).medicationDisplay) {
      return (med as any).medicationDisplay;
    }
    return (
      (med.medication as any)?.display ||
      med.medicationCodeableConcept?.text ||
      med.medicationCodeableConcept?.coding?.[0]?.display ||
      `Medication ${med.id || 'Unknown'}`
    );
  };

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
      if (Notification.permission === 'default') {
        Notification.requestPermission().then((permission) => {
          setNotificationPermission(permission);
        });
      }
    }
  }, []);

  // Load reminders from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        const remindersMap = new Map<string, MedicationReminder>();
        Object.entries(parsed).forEach(([key, value]) => {
          remindersMap.set(key, value as MedicationReminder);
        });
        setReminders(remindersMap);
      }
    } catch (error) {
      console.error('Error loading reminders from localStorage:', error);
    }
  }, []);

  // Initialize reminders for medications that don't have them
  useEffect(() => {
    const updatedReminders = new Map(reminders);
    let hasChanges = false;

    medications.forEach((med) => {
      const medId = med.id || extractMedicationName(med);
      if (!updatedReminders.has(medId)) {
        updatedReminders.set(medId, {
          medicationId: medId,
          medicationName: extractMedicationName(med),
          times: [],
          enabled: false,
        });
        hasChanges = true;
      } else {
        // Update medication name in case it changed
        const existing = updatedReminders.get(medId)!;
        const currentName = extractMedicationName(med);
        if (existing.medicationName !== currentName) {
          existing.medicationName = currentName;
          hasChanges = true;
        }
      }
    });

    if (hasChanges) {
      setReminders(updatedReminders);
      saveReminders(updatedReminders);
    }
  }, [medications]);

  // Save reminders to localStorage
  const saveReminders = (remindersToSave: Map<string, MedicationReminder>) => {
    try {
      const obj = Object.fromEntries(remindersToSave);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(obj));
    } catch (error) {
      console.error('Error saving reminders to localStorage:', error);
    }
  };

  // Check for upcoming reminders and send notifications
  useEffect(() => {
    const checkUpcomingReminders = () => {
      const now = new Date();
      const currentMinutes = now.getHours() * 60 + now.getMinutes();
      const upcoming: Array<{
        medicationName: string;
        time: string;
        minutesUntil: number;
      }> = [];

      reminders.forEach((reminder) => {
        if (!reminder.enabled || reminder.times.length === 0) return;

        reminder.times.forEach((timeStr) => {
          const [hours, minutes] = timeStr.split(':').map(Number);
          const reminderMinutes = hours * 60 + minutes;
          let minutesUntil = reminderMinutes - currentMinutes;

          // If the reminder time has passed today, check for tomorrow
          if (minutesUntil < 0) {
            minutesUntil += 24 * 60; // Add 24 hours
          }

          // Show reminders within the next 2 hours
          if (minutesUntil <= 120) {
            upcoming.push({
              medicationName: reminder.medicationName,
              time: timeStr,
              minutesUntil,
            });
          }

          // Send notification if it's time (within 1 minute) and we haven't notified yet
          const notificationKey = `${reminder.medicationId}-${timeStr}-${now.toDateString()}`;
          if (minutesUntil >= 0 && minutesUntil <= 1 && !notifiedTimes.has(notificationKey)) {
            if ('Notification' in window && notificationPermission === 'granted') {
              new Notification(`Time to take ${reminder.medicationName}`, {
                body: `It's time to take your medication: ${reminder.medicationName} at ${timeStr}`,
                icon: '/vite.svg',
                tag: notificationKey,
              });
              setNotifiedTimes((prev) => new Set(prev).add(notificationKey));
            }
          }
        });
      });

      // Sort by time until reminder
      upcoming.sort((a, b) => a.minutesUntil - b.minutesUntil);
      setUpcomingReminders(upcoming);
    };

    checkUpcomingReminders();
    const interval = setInterval(checkUpcomingReminders, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [reminders, notificationPermission, notifiedTimes]);

  const handleToggleReminder = (medId: string) => {
    const updatedReminders = new Map(reminders);
    const reminder = updatedReminders.get(medId);
    if (reminder) {
      reminder.enabled = !reminder.enabled;
      setReminders(updatedReminders);
      saveReminders(updatedReminders);
    }
  };

  const handleAddTime = (medId: string, time: string) => {
    const updatedReminders = new Map(reminders);
    const reminder = updatedReminders.get(medId);
    if (reminder && !reminder.times.includes(time)) {
      reminder.times.push(time);
      reminder.times.sort(); // Sort times
      setReminders(updatedReminders);
      saveReminders(updatedReminders);
    }
  };

  const handleRemoveTime = (medId: string, time: string) => {
    const updatedReminders = new Map(reminders);
    const reminder = updatedReminders.get(medId);
    if (reminder) {
      reminder.times = reminder.times.filter((t) => t !== time);
      setReminders(updatedReminders);
      saveReminders(updatedReminders);
    }
  };

  const formatTimeUntil = (minutes: number): string => {
    if (minutes < 1) return 'Now';
    if (minutes < 60) return `in ${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (mins === 0) return `in ${hours} hr`;
    return `in ${hours} hr ${mins} min`;
  };

  if (medications.length === 0) {
    return null;
  }

  return (
    <div className="medication-reminders-container">
      <div className="reminders-header">
        <div className="header-top">
          <h4>⏰ Medication Reminders</h4>
          {notificationPermission === 'granted' && (
            <span className="notification-status enabled">🔔 Notifications enabled</span>
          )}
          {notificationPermission === 'denied' && (
            <span className="notification-status disabled">🔕 Notifications blocked</span>
          )}
          {notificationPermission === 'default' && 'Notification' in window && (
            <button
              type="button"
              className="enable-notifications-btn"
              onClick={async () => {
                const permission = await Notification.requestPermission();
                setNotificationPermission(permission);
              }}
            >
              Enable Notifications
            </button>
          )}
        </div>
        <p className="reminders-subtitle">Set reminders to help you remember when to take your medications</p>
      </div>

      {upcomingReminders.length > 0 && (
        <div className="upcoming-reminders-alert">
          <div className="alert-header">
            <span className="alert-icon">🔔</span>
            <strong>Upcoming Reminders</strong>
          </div>
          <div className="upcoming-list">
            {upcomingReminders.slice(0, 3).map((reminder, index) => (
              <div key={index} className="upcoming-item">
                <span className="medication-name">{reminder.medicationName}</span>
                <span className="reminder-time">{reminder.time}</span>
                <span className="time-until">{formatTimeUntil(reminder.minutesUntil)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="reminders-list">
        {medications.map((medication) => {
          const medId = medication.id || extractMedicationName(medication);
          const reminder = reminders.get(medId);
          const medicationName = extractMedicationName(medication);
          const isEditing = editingId === medId;

          if (!reminder) return null;

          return (
            <div key={medId} className="reminder-item">
              <div className="reminder-item-header">
                <div className="reminder-medication-info">
                  <span className="medication-name">{medicationName}</span>
                  {reminder.enabled && reminder.times.length > 0 && (
                    <span className="reminder-status active">
                      {reminder.times.length} reminder{reminder.times.length !== 1 ? 's' : ''} set
                    </span>
                  )}
                </div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={reminder.enabled}
                    onChange={() => handleToggleReminder(medId)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>

              {reminder.enabled && (
                <div className="reminder-times-section">
                  <div className="times-list">
                    {reminder.times.map((time, index) => (
                      <div key={index} className="time-badge">
                        <span>{time}</span>
                        <button
                          type="button"
                          className="remove-time-btn"
                          onClick={() => handleRemoveTime(medId, time)}
                          aria-label={`Remove reminder at ${time}`}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  {isEditing ? (
                    <div className="add-time-form">
                      <input
                        type="time"
                        className="time-input"
                        onBlur={(e) => {
                          if (e.target.value) {
                            handleAddTime(medId, e.target.value);
                            e.target.value = '';
                          }
                          setEditingId(null);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && e.currentTarget.value) {
                            handleAddTime(medId, e.currentTarget.value);
                            e.currentTarget.value = '';
                            setEditingId(null);
                          }
                          if (e.key === 'Escape') {
                            setEditingId(null);
                          }
                        }}
                        autoFocus
                      />
                      <button
                        type="button"
                        className="cancel-btn"
                        onClick={() => setEditingId(null)}
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="add-time-btn"
                      onClick={() => setEditingId(medId)}
                    >
                      + Add Reminder Time
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

