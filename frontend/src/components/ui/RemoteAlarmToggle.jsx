import React, { useState } from 'react';
import { Button } from './Button';
import { BellRing, BellOff } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const RemoteAlarmToggle = ({ labId }) => {
  const { apiFetch } = useAuth();
  const [isAlarmOn, setIsAlarmOn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const toggleAlarm = async () => {
    const newState = !isAlarmOn;
    setIsLoading(true);
    try {
      await apiFetch(`/api/sensors/nodes/${labId}/remote_alarm`, {
        method: 'POST',
        body: JSON.stringify({ status: newState ? 'on' : 'off' })
      });
      setIsAlarmOn(newState);
    } catch (err) {
      alert(`Failed to turn alarm ${newState ? 'ON' : 'OFF'}: ${err.message}`);
    }
    setIsLoading(false);
  };

  return (
    <Button 
      variant={isAlarmOn ? 'danger' : 'secondary'} 
      size="sm" 
      onClick={toggleAlarm}
      disabled={isLoading}
      title={isAlarmOn ? "Turn Remote Alarm OFF" : "Turn Remote Alarm ON"}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '0 12px'
      }}
    >
      {isAlarmOn ? <BellRing size={14} /> : <BellOff size={14} />}
      {isAlarmOn ? 'Alarm ON' : 'Alarm OFF'}
    </Button>
  );
};

export default RemoteAlarmToggle;
