'use client';

import { useState } from 'react';
import ActionableAlertCard from './ActionableAlertCard';

interface Alert {
  id: string;
  menu_item_id: string;
  alert_type: string;
  old_value: string | null;
  new_value: string | null;
  change_percentage: string | number | null;
  is_acknowledged: boolean;
  created_at: string;
  item_name: string | null;
  competitor_name: string | null;
}

interface AlertsListProps {
  initialAlerts: Alert[];
}

export default function AlertsList({ initialAlerts }: AlertsListProps) {
  const [alerts, setAlerts] = useState<Alert[]>(initialAlerts);

  const handleAcknowledge = (id: string) => {
    setAlerts(prev =>
      prev.map(alert =>
        alert.id === id ? { ...alert, is_acknowledged: true } : alert
      )
    );
  };

  // Sort alerts: unacknowledged first, then by date
  const sortedAlerts = [...alerts].sort((a, b) => {
    if (a.is_acknowledged !== b.is_acknowledged) {
      return a.is_acknowledged ? 1 : -1;
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className="space-y-4">
      {sortedAlerts.map((alert) => (
        <ActionableAlertCard
          key={alert.id}
          alert={alert}
          onAcknowledge={handleAcknowledge}
        />
      ))}
    </div>
  );
}
